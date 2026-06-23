import sys
import subprocess

def run_command(command):
    print(f"Executing: {' '.join(command)}")
    try:
        # Use stdout/stderr real-time stream to show progress to user
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        if rc != 0:
            raise subprocess.CalledProcessError(rc, command)
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        sys.exit(1)

def main():
    print("🚀 Starting Successful Safaris cPanel dependency installation...\n")
    
    # 1. Upgrade pip, setuptools, and wheel
    print("📦 Step 1: Upgrading pip, setuptools, and wheel inside virtual environment...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    print("✅ Pip utilities upgraded successfully!\n")
    
    # 2. Install psycopg2-binary forcing pre-compiled binary matching
    print("📦 Step 2: Fetching pre-compiled binary wheel for psycopg2-binary...")
    run_command([sys.executable, "-m", "pip", "install", "psycopg2-binary", "--only-binary=:all:"])
    print("✅ psycopg2-binary installed successfully!\n")
    
    # 3. Install remaining dependencies
    print("📦 Step 3: Installing remaining packages from requirements.txt...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ All dependencies from requirements.txt installed successfully!\n")
    
    print("🎉 Installation complete! All Python dependencies are configured.")

if __name__ == '__main__':
    main()
