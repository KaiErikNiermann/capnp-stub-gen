---
applyTo: '**/*.py'
---
- Use list-comprehension where reasonable over things like for + if 
- Prefer match case statements over if-else chains if reasonable 
- Use strict typing where possible in normal code files, if unreasonable append a `# type: ignore` to the line 
- Autogenerate stub files using pylance/pyrights stub generator if the editor complains about missing stub files 
- For debugging use proper logging, if its not setup yet then set it up first and remember to disable logging when doing a standard run to not spam the stdout/stderr