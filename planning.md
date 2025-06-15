# Planning Document: Modern School Management System

This document outlines the development plan for the Modern School Management System. The goal is to create a simple, functional application based on the requirements in the PRD (v2.3), avoiding complex architectural overhead.

---

## Phase 0: Project Setup & Configuration

This phase focuses on preparing the development environment and initializing the project structure.

* **Step 1: Environment Setup**
    * Install necessary software: Python (for Django), Node.js (for Next.js), PostgreSQL, and Redis.
    * Set up virtual environments for both backend and frontend projects.

* **Step 2: Initialize Repositories**
    * Create a Git repository for the project.
    * Set up two main directories: `/backend` and `/frontend`.

* **Step 3: Backend Project Initialization**
    * [cite_start]Initialize a Django project in the `/backend` directory.
    * Install core dependencies: `Django`, `djangorestframework`, `psycopg2-binary`, `celery`, `redis`.
    * [cite_start]Configure `settings.py` for database connection to PostgreSQL  and basic project settings.

* **Step 4: Frontend Project Initialization**
    * [cite_start]Initialize a Next.js 15 project in the `/frontend` directory.
    * Install core dependencies: `tailwindcss`.
    * [cite_start]Set up Shadcn UI for component architecture.

---

## Phase 1: Backend Development (Django API)

This phase focuses on building the core logic, database models, and API endpoints.

* **Step 1: Database Models**
    * **User Models**: Create a custom User model inheriting from Django's base user to include roles (Super Admin, School Owner, Teacher, Student, Parent, Office Account).
    * **School Models**:
        * [cite_start]`School`: Fields for `name`, `address`, `contact_email`, `contact_number`, `logo`, `dashboard_primary_color`, `dashboard_secondary_color`, `smtp_settings`. Linked to a School Owner.
        * [cite_start]`SchoolGroup`: To group schools under one owner.
    * **Academic Models**:
        * `AcademicSession`, `Term`.
        * `Class` (e.g., Grade 5A).
        * `Subject`.
        * [cite_start]`TeacherAssignment`: Linking teachers to classes and subjects.
    * **Student Models**:
        * `Student`: Linked to a `School`, `Class`, and `Parent` user.
        * `Enrollment`.
    * **Financial Models**:
        * `FeeRecord`: To track student fees. Fields for `student`, `amount`, `status` (e.g., "Cleared", "Pending").
    * **Grading Models**:
        * `Result`: Linking `student`, `subject`, `term`. [cite_start]Fields for `first_ca`, `second_ca`, `exam_marks`.

* **Step 2: API Endpoints & Logic**
    * **Authentication**: Set up token-based authentication (e.g., JWT) for API access.
    * [cite_start]**Permissions**: Implement role-based permissions to restrict access based on user type (e.g., only Teachers can input grades, only owners can change school settings).
    * **Super Admin Endpoints (`/api/superadmin/`)**:
        * [cite_start]`POST /owners/`: Add a new School Owner.
        * [cite_start]`GET, PUT /owners/{id}/`: View/Edit a School Owner.
        * [cite_start]`GET, PUT /schools/{id}/`: View/Modify any school's records.
    * **School Owner Endpoints (`/api/owner/`)**:
        * [cite_start]`GET /dashboard/`: Fetch summary metrics for the owner's schools.
        * [cite_start]`PUT /schools/{id}/customize/`: Update school logo, colors, info.
        * [cite_start]`PUT /schools/{id}/smtp/`: Update SMTP settings.
        * [cite_start]`POST /users/manage`: Add teachers, students, office accounts.
        * [cite_start]`POST /academics/setup`: Define classes, subjects, terms.
    * **Teacher Endpoints (`/api/teacher/`)**:
        * [cite_start]`GET /dashboard/`: Get assigned classes.
        * [cite_start]`POST /grades/input/`: Endpoint to submit `1st CA`, `2nd CA`, and `Exam` marks for students in an assigned class.
    * **Student Endpoints (`/api/student/`)**:
        * [cite_start]`GET /profile/`: Fetch student's profile info.
        * [cite_start]`GET /results/`: Fetch termly results, but only if their fee status is "Cleared".
    * **Financials Endpoints (`/api/office/`)**:
        * `POST /fees/import`: Bulk import fee records.
        * `PUT /fees/student/{id}`: Update a student's fee status.
    * **API Documentation**: Generate Swagger (OpenAPI) documentation for all endpoints.

* **Step 3: Asynchronous Tasks**
    * [cite_start]Configure Celery and Redis.
    * [cite_start]Create a task to send an email to a parent when their child's results are generated. [cite_start]This task will use the school's specific SMTP settings.

---

## Phase 2: Frontend Development (Next.js)

This phase focuses on building the user interfaces for each role.

* **Step 1: Core UI & Layout**
    * Create a main layout component with a sidebar/navigation.
    * [cite_start]Develop a set of reusable UI components using **Shadcn UI/Tailwind CSS** (Buttons, Forms, Tables, Modals).
    * Implement login/logout functionality.

* **Step 2: Super Admin Dashboard**
    * [cite_start]Create a view to list all school owners and schools.
    * [cite_start]Build forms (in modals) to add/edit school owners.

* **Step 3: School Owner Dashboard**
    * [cite_start]**Main Dashboard**: Display key metrics.
    * [cite_start]**School Settings Page**: Build forms to upload a school logo, set the school name/address, and configure theme colors and SMTP settings.
    * [cite_start]**User Management Page**: Create tables to display teachers and students, with buttons to add new users.
    * [cite_start]**Academics Page**: Interface to define classes and subjects.
    * [cite_start]**Results Page**: View to see the `Class Result Summary` table for generated results.

* **Step 4: Teacher Dashboard**
    * [cite_start]**Main Dashboard**: Display a list of assigned classes.
    * **Grade Entry Page**:
        * Allow the teacher to select a class, subject, and term.
        * Display a table of students in that class.
        * [cite_start]Provide input fields for `1st CA`, `2nd CA`, and `Exam` marks for each student.

* **Step 5: Student Dashboard**
    * [cite_start]**Profile Page**: View profile information and update profile image.
    * **Results Page**:
        * [cite_start]Display the student's termly results in a table as specified in the PRD.
        * If fee status is not "Cleared", show a message indicating results are unavailable.
        * [cite_start]Include a "Download as PDF" button.

---

## Phase 3: Integration, Testing & Deployment

This final phase connects the backend and frontend, ensures functionality, and prepares for release.

* **Step 1: API Integration**
    * Connect the Next.js frontend components to the Django API endpoints.
    * Implement token handling on the frontend to manage user sessions.
    * Ensure data flows correctly between the two systems.

* **Step 2: Testing**
    * **Backend**: Write basic unit tests for critical logic (e.g., result calculation, fee status checks).
    * **Frontend**: Conduct manual user-flow testing for each user role.
        * Can a School Owner customize their school?
        * Can a Teacher input grades correctly?
        * Can a Student view and download their results (and are they blocked if fees are unpaid)?
        * Are emails sent upon result generation?
    * **Cross-browser Testing**: Perform quick checks on major browsers (Chrome, Firefox).

* **Step 3: Deployment (Simple)**
    * **Backend**: Deploy the Django application (e.g., using Gunicorn and Nginx on a cloud server).
    * **Frontend**: Deploy the Next.js application (e.g., using Vercel or as a static build served by Nginx).
    * **Database**: Set up a production PostgreSQL database instance.
    * **Final Configuration**: Ensure all environment variables (database URLs, secret keys) are correctly set in the production environment.