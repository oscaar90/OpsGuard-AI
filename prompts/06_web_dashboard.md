**Role:** Act as a Senior Frontend Engineer and UX expert for developer tools (DevTools).

**Objective:**
Create a simple yet visually impactful web application ("Mission Control Dashboard") named **OpsGuard Monitor**.
This web app will serve as a graphical interface to visualize the blocks and approvals performed by our security CLI (OpsGuard-AI) within CI/CD pipelines.

**Tech Stack:**
- Framework: Next.js 14+ (App Router, TypeScript).
- Styling: Tailwind CSS (Dark Mode by default).
- Icons: Lucide React.
- API Client: Octokit (GitHub REST API).
- UI/Charts Library: Native components with Tailwind (to avoid bloatware).

**Functional Requirements:**
1. **API Connection:** The web app must connect to the GitHub Actions API of a public/private repository using a Token (PAT).
2. **Business Logic:**
   - If a Workflow Run has `conclusion: "failure"`, it is considered **BLOCKED** by OpsGuard.
   - If it has `conclusion: "success"`, it is considered **APPROVED**.
3. **KPIs:** Display cards with: Total Scans, Block Rate (%), Blocked Threats.
4. **Real-time Feed:** A table showing the latest commits, their author, message, and whether they passed the security check or not.

**Generation Instructions:**

Provide, step-by-step and in copy-paste ready code blocks:

1. **Initialization Commands:**
   - The `npx` command to create a clean Next.js project (non-interactive).
   - The `npm install` command for necessary dependencies (`@octokit/rest`, `lucide-react`, `date-fns`, etc.).

2. **Environment Configuration:**
   - The content for the `.env.local` file required to configure `NEXT_PUBLIC_GITHUB_TOKEN`, `OWNER`, and `REPO`.

3. **Source Code (`src/app/page.tsx`):**
   - A single robust file containing all logic (data fetching) and UI.
   - **Design:** Professional "Cyberpunk/Hacker" aesthetic. Dark background (`bg-gray-950`), technical gray text, with accents in Green (Approved), Red (Blocked), and Blue (System).
   - It must handle loading states ("Initializing Telemetry...") and connection errors.

**Note:** I do not want a backend or database. The application must be purely Client-Side Rendering (CSR) with `use client` to facilitate Vercel deployment or immediate local execution.