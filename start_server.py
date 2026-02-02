import sys
import os
import subprocess

def main():
    # Ensure current dir is in python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = current_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    try:
        # Run uvicorn directly as a module
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=current_dir,
            env=env
        )
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
