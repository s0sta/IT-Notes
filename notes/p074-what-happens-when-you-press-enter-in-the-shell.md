---
id: p74
title: "What happens when you press Enter in the shell"
slug: what-happens-when-you-press-enter-in-the-shell
sections: [it]
topic: "Linux"
tags: [Linux, Bash, CommandLine, SysAdmin, DevOps]
source: "LinkedIn post P74 · Linux series"
linkedin_date: 2027-03-18
design: pipeline
---

# What happens when you press Enter in the shell

You type ls and press Enter. Before a single file is listed, the shell does six things. Knowing them explains most strange shell errors.

## Quick reference

1. **The shell reads the line** — Splits it into words and expands aliases. · `read`
2. **Expansion** — Variables, ~ and \*.log turn into real values and file names. · `$VAR  *.log`
3. **Find the program** — A function or builtin? If not, search each folder in `$PATH`. · `$PATH`
4. **fork()** — The shell makes a copy of itself: a new child process. · `fork()`
5. **exec()** — The child replaces itself with the program, like `/usr/bin/ls`. · `execve()`
6. **Exit code** — The program ends, the shell waits, and the result goes in `$?`. · `$? = 0`

## Explained

1. **The shell reads the line.** It splits it into words: the command and its arguments. Aliases are expanded here, which is why ll can mean `ls -lah`.

2. **Expansion.** `$HOME` becomes `/home/you`, ~ becomes your home folder, and \*.log becomes the list of matching file names. This happens before the command runs, which is why quoting matters. rm $file with a space in the name becomes two arguments.

3. **Find the program.** Is it a shell function or a builtin like cd? If not, the shell searches every folder in `$PATH`, in order, and uses the first match. "command not found" means it searched them all. type ls tells you what the shell will actually run.

4. **fork().** The shell creates a copy of itself, a child process. The parent shell keeps running and waits.

5. **exec().** The child replaces itself with the real program, for example `/usr/bin/ls`. Same process ID, completely new code.

6. **Exit code.** The program finishes, the shell collects its exit status and stores it in `$?`. Zero means success, anything else is an error. This is what && and || in scripts are checking.

> **Why this matters in practice:** a script that works in your terminal but not in cron is usually step 3, a different PATH. A command that breaks on file names with spaces is step 2. And builtins like cd cannot be a separate program, because a child process cannot change the parent's directory.

## In one line

> **Every command is fork, exec, wait.** Know the steps, and shell errors start to make sense.

**See it yourself**

```bash
type ls; echo $PATH; ls /nope; echo $?
```
