# Master Document 7: Increment 1 Deep Dive - Foundation & Farmer Dashboard
**Project Name:** Agri-Grid: Smart Agriculture & Food Security Ecosystem
**Project Lead:** Ameer Muawiyah (Project Manager & Lead Data Architect)
**Context:** Detailed Step-by-Step Execution Plan for Increment 1

## 1. Increment Objective
**Goal:** Establish the core system infrastructure, implement Role-Based Access Control (RBAC), and build a functional Farmer Dashboard allowing users to execute CRUD (Create, Read, Update, Delete) operations on their crop data. This establishes the "Supply Side" data generation necessary for all future increments.

## 2. Step-by-Step Workflow Reasoning
1.  **System Blueprinting:** We draft UML diagrams and API structures first. Coding blindly leads to database conflicts and disjointed frontend-backend communication.
2.  **Database & Backend Initialization:** The SQL database and Flask/Django server are created to provide a secure environment. Data isolation (Zero-Trust) is strictly enforced from day one.
3.  **Frontend Development:** The visual interfaces are designed to be mobile-responsive, allowing farmers to interact easily with the system.
4.  **System Integration & V&V:** We connect the frontend to the backend, resolve Cross-Origin Resource Sharing (CORS) or routing issues, and execute test scripts to guarantee stability before moving to Increment 2.

## 3. Agent Task Delegation Plan
To maximize efficiency, the workload is distributed across four specialized AI Agents acting under the supervision of the Project Manager.

### A. Requirements and Architecture Agent
*   **Role:** Chief of Blueprints and Requirements.
*   **Tasks:**
    1.  Draft the exact SRS constraints for the Farmer Login and active crop CRUD operations.
    2.  Design architectural sequence diagrams mapping how data flows from the Farmer UI, through the Backend, to the SQL Database.
    3.  Define the strict JSON payload structures (keys, value types) that the frontend will transmit to the backend for crop creation.

### B. UI/UX Agent
*   **Role:** Frontend Developer.
*   **Tasks:**
    1.  Design wireframes for a mobile-responsive Login Screen and the main Farmer Dashboard.
    2.  Write the HTML, CSS, and JavaScript for these pages.
    3.  Implement fetch/axios logic in the JS to `POST` and `GET` the JSON payloads defined by the Architecture Agent.

### C. Database and Backend Agent
*   **Role:** Database Administrator (DBA) & Core Backend Engineer.
*   **Tasks:**
    1.  Write ACID-compliant SQL schemas to generate the `Users`, `Farmers`, and `Listings` tables. Ensure strict normalization.
    2.  Initialize the core Flask/Django web server.
    3.  Develop the secure RBAC login route, ensuring it generates session tokens and securely routes valid farmers to `/dashboard/farmer`.
    4.  Build the backend API endpoints (e.g., `/api/crops`) that process incoming JSON payloads and execute the required SQL CRUD commands.

### D. Main Workspace Agent (CTO & Integration Hub)
*   **Role:** QA Lead, DevOps, and Integration Master.
*   **Tasks:**
    1.  Initialize the centralized GitHub repository and configure branch protection rules.
    2.  **System Integration:** Merge the frontend HTML/JS output with the backend Python/SQL infrastructure.
    3.  **Cross-Domain Debugging:** Execute end-to-end testing of the Farmer login and crop creation flow. Identify and resolve any API handshaking errors, database connection bugs, or security misconfigurations.
    4.  Revise the Master Documents if the database schema or API structures required modification during the integration phase.
