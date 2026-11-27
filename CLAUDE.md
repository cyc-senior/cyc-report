@AGENTS.md

## Claude Code notes

- Talk with the user in Thai unless they write in English.
- The monorepo is usually at `D:\cyc-monorepo` on this machine; read code and `git log` there for facts.
- On Windows the Bash tool can eat backslashes in heredocs/inline scripts (`\\section` becomes `\section`).
  Write helper scripts to a file with the Write tool and run them, rather than inlining LaTeX regexes.
