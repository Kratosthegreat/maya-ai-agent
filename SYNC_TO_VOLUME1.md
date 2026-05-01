# Sync fixes to `/volume1/docker/maya-ai-agent`

Run these commands on the target machine:

```bash
cd /volume1/docker/maya-ai-agent
git status

# Add this repo as a temporary remote (replace URL)
git remote add codex-work <YOUR_WORKSPACE_REPO_URL>
git fetch codex-work

# Cherry-pick the fixes
# 1) Expand subsystem
# 2) Runtime bug fixes (action_plan scope, optional import, complexity gating, timezone)
git cherry-pick c2cf523
git cherry-pick 8e1fa08

# Run checks
python -m py_compile main.py super_agent.py test_super_agent.py
pytest -q test_super_agent.py
```

If your target repo has diverged, use:

```bash
git cherry-pick -m 1 <commit>  # if merge commit
git cherry-pick --abort        # to cancel
```

Or copy files directly:
- `main.py`
- `super_agent.py`
- `test_super_agent.py`
- `README.md`
