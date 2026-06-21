import os
import subprocess
import time
import requests
import sys
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser

# 1. Stack-based HTML Parser to extract links and detect if they are inside navigation areas
class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.tag_stack = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k: v for k, v in attrs if v is not None}
        
        # Check if the tag itself or its attributes indicate a nav container
        is_nav_element = (
            (tag == 'nav') or 
            ('nav' in attrs_dict.get('class', '').lower()) or 
            ('nav' in attrs_dict.get('id', '').lower()) or
            (attrs_dict.get('role') == 'navigation')
        )
        
        self.tag_stack.append({
            "tag": tag,
            "is_nav": is_nav_element,
            "class": attrs_dict.get('class', ''),
            "id": attrs_dict.get('id', '')
        })

        if tag == 'a':
            href = attrs_dict.get('href', '').strip()
            # Determine if this <a> is inside any nav container in our current path stack
            is_nav = any(
                t['is_nav'] or 
                'nav' in t['class'].lower() or 
                'nav' in t['id'].lower() 
                for t in self.tag_stack
            )
            self.current_link = {
                "href": href,
                "is_nav": is_nav,
                "text": ""
            }

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link["text"] += data

    def handle_endtag(self, tag):
        if self.tag_stack:
            self.tag_stack.pop()
        if tag == 'a' and self.current_link is not None:
            self.current_link["text"] = self.current_link["text"].strip()
            self.links.append(self.current_link)
            self.current_link = None

def clean_url(base_url, href):
    # Resolve relative URL
    abs_url = urljoin(base_url, href)
    # Strip fragment and whitespace
    parsed = urlparse(abs_url)
    cleaned = parsed._replace(fragment='').geturl()
    return cleaned

def is_internal(url, base_domain):
    parsed = urlparse(url)
    if not parsed.netloc:
        return True
    return parsed.netloc == base_domain

def run_audit():
    start_time = time.time()
    base_url = "http://127.0.0.1:8000"
    base_domain = "127.0.0.1:8000"
    
    print("--- Starting Local Django Server ---")
    server_process = subprocess.Popen(
        ["venv/bin/python", "manage.py", "runserver", "127.0.0.1:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    server_started = False
    for i in range(15):
        try:
            r = requests.get(base_url, timeout=1)
            print("Server responded successfully. Proceeding to crawl.")
            server_started = True
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
            
    if not server_started:
        print("[CRITICAL] Could not connect to Django server on port 8000. Aborting.")
        server_process.terminate()
        sys.exit(1)

    # Crawling state
    queue = [(base_url, 0)]  # (url, depth)
    visited_internal = set()  # set of internal URLs we have parsed/requested for child links
    tested_urls = {}  # url -> {"status": code/error, "text": link_text, "source": source_page, "is_nav": is_nav}
    tested_nav_urls = set()  # set of unique nav URLs tested to enforce the 15 limit
    
    # Audit Limits
    MAX_DEPTH = 3
    MAX_NAV_LINKS = 15
    TIMEOUT_SECONDS = 280  # 4 minutes 40 seconds to safely stay under the 5 minute limit

    print("\n--- Auditing Links ---")
    
    while queue:
        # Check overall timeout boundary
        if time.time() - start_time > TIMEOUT_SECONDS:
            print("[WARNING] Nearing 5-minute timeout boundary. Stopping crawl.")
            break
            
        current_url, depth = queue.pop(0)
        
        # If internal and not parsed yet, parse for child links
        if is_internal(current_url, base_domain):
            if current_url in visited_internal:
                continue
            visited_internal.add(current_url)
            
            # Fetch and parse the page
            try:
                # Add a reasonable request timeout
                resp = requests.get(current_url, timeout=5, allow_redirects=True)
                final_status = resp.status_code
                
                # Update status of this URL in tested_urls if it wasn't there
                if current_url not in tested_urls:
                    tested_urls[current_url] = {
                        "status": final_status,
                        "text": "Self (Root/Page)",
                        "source": "Initial Queue",
                        "is_nav": False
                    }
                else:
                    tested_urls[current_url]["status"] = final_status

                if final_status == 200:
                    # Parse links if we haven't reached depth limit
                    if depth < MAX_DEPTH:
                        parser = LinkExtractor()
                        parser.feed(resp.text)
                        
                        for link in parser.links:
                            href = link["href"]
                            if not href or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
                                continue
                                
                            target_url = clean_url(current_url, href)
                            is_nav = link["is_nav"]
                            text = link["text"] or "[Image/Empty Text]"
                            
                            # Normalize internal target urls to use absolute url
                            is_target_internal = is_internal(target_url, base_domain)
                            
                            # Decide whether to test this URL
                            if is_nav:
                                # If it's a primary nav link, check if we've already tested it or if we can test it
                                if target_url in tested_nav_urls:
                                    # Already tested or queued as nav, skip redundant check
                                    pass
                                else:
                                    if len(tested_nav_urls) >= MAX_NAV_LINKS:
                                        # Skip testing to enforce max 15 primary nav limit
                                        continue
                                    tested_nav_urls.add(target_url)
                            
                            # Check if the URL needs to be tested
                            if target_url not in tested_urls:
                                # Test the URL now
                                try:
                                    test_resp = requests.get(target_url, timeout=5, allow_redirects=True)
                                    status_code = test_resp.status_code
                                    # If redirected, we might want to log if the final page is fine
                                    tested_urls[target_url] = {
                                        "status": status_code,
                                        "text": text,
                                        "source": current_url,
                                        "is_nav": is_nav
                                    }
                                    print(f"[TESTED] {target_url} -> {status_code} (Depth: {depth+1}, Nav: {is_nav})")
                                except Exception as e:
                                    tested_urls[target_url] = {
                                        "status": f"Error: {type(e).__name__}",
                                        "text": text,
                                        "source": current_url,
                                        "is_nav": is_nav
                                    }
                                    print(f"[FAILED] {target_url} -> Connection Error (Depth: {depth+1}, Nav: {is_nav})")
                            
                            # If internal, and we haven't visited/parsed it yet, and its depth will be <= MAX_DEPTH, enqueue it
                            if is_target_internal and target_url not in visited_internal:
                                # Enqueue for crawling child links
                                queue.append((target_url, depth + 1))
                                
            except Exception as e:
                # Page load failed
                tested_urls[current_url] = {
                    "status": f"Error: {type(e).__name__}",
                    "text": "Self",
                    "source": "Queue Processing",
                    "is_nav": False
                }
                print(f"[FAILED] Could not request internal URL {current_url}: {e}")

    # Terminate server
    print("\n--- Shutting Down Server ---")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()

    # Process and log results
    failures = []
    successes = []
    
    for url, info in tested_urls.items():
        status = info["status"]
        # Consider non-2xx/3xx codes as failure (and exceptions)
        is_failure = False
        if isinstance(status, int):
            if status < 200 or status >= 400:
                is_failure = True
        else:
            is_failure = True  # String exception
            
        record = {
            "URL": url,
            "Source": info["source"],
            "Text": info["text"],
            "Status": status,
            "IsNav": "Yes" if info["is_nav"] else "No"
        }
        if is_failure:
            failures.append(record)
        else:
            successes.append(record)

    # 4. Generate report markdown
    report_md = []
    report_md.append("# Fast-Pass Web Audit Report\n")
    report_md.append(f"**Execution Date/Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_md.append("## Boundaries Enforced\n")
    report_md.append(f"- **Max Crawling Depth:** {MAX_DEPTH} URL levels")
    report_md.append(f"- **Max Primary Navigation Links Tested:** {MAX_NAV_LINKS} (Actual tested/seen: {len(tested_nav_urls)})")
    report_md.append(f"- **Execution Timeout:** 5 minutes (Actual time: {time.time() - start_time:.2f} seconds)\n")
    
    report_md.append("## Audit Statistics\n")
    report_md.append(f"- **Total Links Tested:** {len(tested_urls)}")
    report_md.append(f"- **Total Failures (404 / Broken / Error):** {len(failures)}")
    report_md.append(f"- **Total Successes (2xx/3xx):** {len(successes)}\n")

    report_md.append("## Failures Summary Table\n")
    if failures:
        report_md.append("| Source Page | Link URL | Link Text / Element | Status Code | Navigation Link? |")
        report_md.append("| :--- | :--- | :--- | :--- | :--- |")
        for fail in failures:
            report_md.append(f"| {fail['Source']} | {fail['URL']} | {fail['Text']} | {fail['Status']} | {fail['IsNav']} |")
    else:
        report_md.append("*No failures or broken links detected during the audit!*")
        
    report_md.append("\n## All Audited Links (Reference List)\n")
    report_md.append("| Status | URL | Nav? | Link Text | Found On |")
    report_md.append("| :--- | :--- | :--- | :--- | :--- |")
    for link in sorted(successes + failures, key=lambda x: str(x['Status'])):
        report_md.append(f"| {link['Status']} | {link['URL']} | {link['IsNav']} | {link['Text']} | {link['Source']} |")

    # Output to stdout
    report_content = "\n".join(report_md)
    print("\n--- AUDIT COMPLETED ---")
    print(report_content)
    
    # Save report to workspace
    with open("web_audit_report.md", "w") as f:
        f.write(report_content)
    print("\nReport written to backend/web_audit_report.md")

if __name__ == "__main__":
    run_audit()
