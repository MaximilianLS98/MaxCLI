# Projects and tasks

Register directories without modifying their contents:

```sh
max project add maxcli ~/developer/MaxCLI --tag personal --editor 'code --wait'
max project list --tag personal
max project list max --json
max project open maxcli
max project open                  # interactive selection
max project show maxcli --json
max project remove maxcli        # removes registration only
```

Names can be abbreviated when the match is unique. Editor priority is project
file, registration, VISUAL, EDITOR, then `code`. Commands are split into arguments;
paths containing spaces are passed intact. `project open --dry-run` previews the command.

Run `max project init` in a repository to create `.maxcli.json`, then edit it:

```json
{
  "version": 1,
  "editor": ["code"],
  "tasks": {
    "dev": ["npm", "run", "dev"],
    "test": ["npm", "test"],
    "build": {"command": ["npm", "run", "build"], "cwd": ".", "env": {"CI": "true"}}
  },
  "environments": {
    "dev": {
      "env": {"APP_ENV": "development"},
      "ssh_target": "dev-server",
      "gcp_configuration": "development",
      "kubernetes_context": "local",
      "coolify_application": "application-uuid"
    }
  }
}
```

```sh
max run dev
max run --project maxcli test
max run --env dev dev -- --port 3001
max run --dry-run --env dev build
```

Put MaxCLI options **before the task name**. Everything after the task name is
forwarded to the task (an initial `--` is stripped). Tasks inherit the terminal,
run at the project root or their configured relative `cwd`, and preserve exit
codes. Discovery walks parent directories and chooses the closest registered
project or `.maxcli.json` file. Task environment values override selected
environment values, which override inherited variables.

Review task definitions before executing tasks from another repository. Tasks
are explicit argument arrays: no shell expansion happens unless you deliberately
use a shell command such as `["sh", "-c", "..."]`. Adding, listing, showing, or
opening a project never runs task hooks. Do not commit secrets into this file;
use inherited environment variables. Dry-run prints variable names, not values.

SSH/cloud/cluster/deployment associations are project metadata, shown by
`project show --json`; selecting an environment does not change global cloud
credentials or deploy anything. A project can be used without registration when
its directory contains `.maxcli.json`.
