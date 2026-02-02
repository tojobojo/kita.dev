import argparse
import logging
import sys
import os

# Ensure the current directory is in the path so imports work correctly
sys.path.append(os.getcwd())

from agent.controller import AgentController

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    parser = argparse.ArgumentParser(description="Kita.dev Autonomous Agent CLI")
    parser.add_argument("task", help="The natural language task to execute")
    parser.add_argument("--repo", default=os.getcwd(), help="Path to the repository to work on (default: current dir)")
    
    args = parser.parse_args()
    
    setup_logging()
    
    task = args.task
    repo_path = os.path.abspath(args.repo)
    
    print(f"Starting Agent...")
    print(f"Task: {task}")
    print(f"Repository: {repo_path}")
    
    try:
        controller = AgentController()
        final_state = controller.run(task, repo_path)
        print(f"\nAgent execution finished.")
        print(f"Final State: {final_state}")
        
        if final_state in ["STOPPED_SAFE", "STOPPED_ERROR", "TESTS_FAILED"]:
             sys.exit(1)
        
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
