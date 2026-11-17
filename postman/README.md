# Library API in Postman

This collection contains all 16 library operations, organized into Books, Members,
Loans, and Reports, plus a Documentation folder for Swagger UI and OpenAPI JSON.
Requests, bodies, status codes, and saved response examples come from the existing
Flask API and `../openapi.json`. Saved examples are illustrative snapshots; dates,
IDs, balances, and list contents depend on your database.

## Import and start

1. In Postman, choose **Import** and select `Library-API.postman_collection.json`.
2. Import `Local.postman_environment.json` and select **Local** as the active
   environment using the environment selector.
3. From the repository root, start Flask in PowerShell:

   ```powershell
   .\.venv\Scripts\python.exe -B -m flask run --port 8000
   ```

   If an older server is already using port 8000, stop that server and restart it
   from this repository. Alternatively use another port and update `baseUrl`.

4. Confirm `baseUrl` is `http://localhost:8000`, without a trailing slash. Open a
   read-only request such as **Books / List books**, then select **Send**.

## Resource IDs and request bodies

The environment includes `bookId`, `memberId`, and `loanId`, each initially `1`.
These are examples, not guaranteed records. Use **List books**, **List members**,
and **List loans** to find real IDs, then edit the corresponding active environment
values. A loan ID is different from a book ID. Check availability, membership
balance, and loan state before sending a mutation.

Successful **Add a book**, **Register a member**, and **Check out a book** requests
save the integer `id` from their actual JSON response into the corresponding
collection variable. They also update that variable in the active environment if
it exists there, because environment values take precedence over collection
values. Failed requests or responses without a positive integer ID preserve saved
values. Do not define conflicting local/data variables when running these requests.

Checkout uses numeric `{{bookId}}` and `{{memberId}}` substitutions in its JSON
body. The raw template becomes valid JSON after Postman resolves these variables;
keep their values as integer IDs. Other example bodies match OpenAPI exactly.
Choose a new valid registration email each time you create a member; resending
`lee@campus.edu` after it has been registered returns 409. No random data or
automatic request chaining is configured.

The optional `available=true` and `overdue=true` query parameters are present but
unchecked by default. Enable them in the **Params** tab to filter lists. Only the
exact lowercase value `true` enables either filter.

## Recommended manual workflow

Send these requests individually, checking each response before continuing:

1. **Members / Register a member** — use a unique email; saves `memberId` (201).
2. **Books / Add a book** — creates an available book; saves `bookId` (201).
3. **Loans / Check out a book** — uses those IDs and saves `loanId` (201).
4. **Loans / Get a loan** — inspect the new loan and `current_fine` (200).
5. Optionally **Loans / Renew a loan** — once, before return, while not overdue
   (200). A second renewal returns 409.
6. **Members / Get member loans and balance** — inspect the account (200).
7. **Loans / Return a book** — marks the book available and stores any fine (200).
8. **Reports / Get overdue report** and **Get library summary** (200).

This ordering crosses folders. Folder order is organizational, not an automatic
workflow; do not use **Run collection** expecting every success assertion to pass.
Renewal after return and payment without a fine deliberately return 409.

To demonstrate **Pay a fine**, use a separate loan with a due date before today:
add the optional `due_date` field to checkout using an ISO date such as yesterday
(`YYYY-MM-DD`), return that loan, then pay its positive unpaid fine. The ordinary
on-time workflow produces no fine, so payment should not succeed there. Verify
`loanId` before payment. Checkout/return/renew/payment responses omit
`current_fine`; only loan list/detail responses include it.

## Changes to local data

- **Add a book** and **Register a member** create records.
- **Check out a book**, **Return a book**, **Renew a loan**, and **Pay a fine**
  update library records and append notifications to `outbox.txt`.
- **Delete a book** permanently deletes an available book. Its pre-request script
  skips the request unless the collection variable `allowDelete` is exactly `true`.
  If you intentionally want to delete your own disposable test book, verify its
  `bookId`, return it first if necessary, temporarily set `allowDelete=true`, send
  **Delete a book** (204, empty body), then restore `allowDelete=false`. Do not
  enable this flag for an entire collection run. No cleanup runs automatically.
- All GET requests, including Documentation, are read-only. Use a browser at
  `{{baseUrl}}/docs` for interactive Swagger UI; Postman receives its HTML.

## Tests and maintenance

Each request checks its expected successful HTTP status. Requests expecting JSON check
that the response parses as JSON; deletion checks an empty body. Errors have saved
examples and descriptions, but a failed prerequisite correctly fails the success
assertion. ID capture happens only on a successful, valid creation response.

Use a current Postman desktop version supporting `pm.execution.skipRequest()` for
the deletion guard. Importing files alone sends no requests. The collection uses
no credentials or machine-specific paths.

When changing the API, update OpenAPI and this collection together, including body
examples, required fields in request descriptions, response examples, and status
tests. Collection/schema validation and local script checks are separate from
execution inside the Postman application; see the audit result in the chat for
which checks were actually performed.
