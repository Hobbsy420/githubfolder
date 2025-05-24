import sys
from scripts import (
    search_jobs,
    update_apply_email,
    apply_to_jobs,
    deduplicate_jobs,
    generate_cover_letters  # <- make sure this line is here
)

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py [command]")
        print("Commands: search_jobs, update_apply_email, deduplicate_jobs, apply_to_jobs, generate_cover_letters")
        return

    cmd = sys.argv[1]

    if cmd == "search_jobs":
        search_jobs.run()
    elif cmd == "update_apply_email":
        update_apply_email.run()
    elif cmd == "deduplicate_jobs":
        deduplicate_jobs.run()
    elif cmd == "apply_to_jobs":
        apply_to_jobs.run()
    elif cmd == "generate_cover_letters":
        generate_cover_letters.run()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
