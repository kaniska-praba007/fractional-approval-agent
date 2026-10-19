# GitHub Branch Protection Setup Guide

This guide details the click-by-click steps to configure branch protection rules for the `main` branch on GitHub.

---

## Click-by-Click Instructions

1. **Navigate to Repository Settings:**
   - Open the GitHub repository in your browser: `https://github.com/kaniska-praba007/fractional-approval-agent`.
   - Click on the **Settings** tab in the top navigation bar.

2. **Access Branch Protection Rules:**
   - In the left sidebar, under **Code and automation**, click **Branches**.
   - Under **Branch protection rules**, click the **Add branch protection rule** (or **Add rule**) button.

3. **Configure Branch Pattern:**
   - In the **Branch name pattern** field, enter: `main`.

4. **Set Protection Policies:**
   - Check **Require a pull request before merging**:
     - **IMPORTANT:** Leave **Require approvals** unchecked (`0` required approvals), or check it only if teammates are online. *The human lead must be able to merge time-critical bug fixes without blocking on approvals near the deadline.*
     - Check **Dismiss stale pull request approvals when new commits are pushed**.
   - Check **Require status checks to pass before merging**:
     - Check **Require branches to be up to date before merging**.
     - In the search bar for status checks, type: `test` (the exact job name defined in `.github/workflows/ci.yml`).
     - Select `test` from the dropdown list.
   - Check **Block force pushes** (ensure "Allow force pushes" is UNCHECKED).
   - Check **Do not allow bypassing the above settings** (or enforce for administrators as appropriate).

5. **Save Changes:**
   - Click **Create** (or **Save changes**) at the bottom of the page.
   - Enter your GitHub password or 2FA confirmation if prompted.

---

## Fallback for GitHub Free Plan on Private Repositories

> [!NOTE]
> On GitHub Free accounts, branch protection rules are only supported on **public** repositories. If the repository is currently set to **private**, GitHub may display a prompt stating that branch protection rules require GitHub Team or Enterprise.

### What to Do If Branch Protection Is Unavailable:
If GitHub does not allow setting branch protection rules on this private repo:
1. **Team Covenant Agreement:** All team members and AI pair programmers commit to the zero-direct-push rule:
   - **Nobody pushes directly to `main` under any circumstances.**
   - All work must be conducted on feature/task branches (`area/task-id-name`).
   - All merges to `main` occur exclusively through GitHub Pull Requests after verifying that automated CI (`pytest -q` and lint guards) is green.
2. **Switch to Public (Post-Evaluation):** When ready for final public submission before the Wednesday deadline, convert the repository to **Public** under **Settings -> Danger Zone -> Change visibility**, and the branch protection rule can then be enabled immediately.
