# Client request (received after the previous developer left)

> **From:** HR team, Northwind Logistics
> **Subject:** AI Pulse pilot: two changes before rollout
>
> Hi team, our legal and HR teams reviewed the AI Pulse pilot and need two changes before we can roll it out:
>
> 1. **No small groups on the dashboard.** If a department has fewer than 5 people who completed the diagnostic, leadership must not see that department's scores or risks on their own. Group them under "Other teams" or hide them, but individuals must never be identifiable.
> 2. **Right to delete.** Any employee must be able to delete all their answers and their report themselves, and it must disappear from every dashboard immediately.
>
> Thanks, Northwind HR

## Implementation status

Both requested changes have been implemented and tested.

1. **Small-group dashboard privacy**
   - Departments with fewer than 5 employees who have completed the diagnostic are hidden from the leadership dashboard.
   - This prevents small groups from exposing individually identifiable scores or risks.

2. **Right to delete**
   - Employees can delete their diagnostic data themselves.
   - Deletion is scoped to the employee's current organization membership, so data from another organization is not deleted accidentally.
   - The employee's report is derived from the deleted response data and therefore no longer contains that diagnostic data.