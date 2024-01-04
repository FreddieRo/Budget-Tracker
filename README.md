# Budget Tracker Web Application
##### Video Demo: https://youtu.be/p3Mr6vDrVYY

### Description:

This web app allows the user to track their budget and their expenses. It uses graphs to visualize the users spending.
The budget tracker was created as the final project for the CS50 Introduction to Computer Science course.


### Key Features:
- Add a **budget**
- Personalise the **duration of the budget**
- **Add expenses** with details, such as a description, amount, category, date, and the type of expense.
- **Generate charts** to visualize spending by category, amount over time, and budget vs actual spending.
- **Customization**: the possiblity to add personalized budgets periods.
- **Filter** the current expenses in a table by category, date, or search term.
- **Separate fixed/recurring expenses** in a different table to manage them.
- **Archive old expenses** to start a new budget.
- **Archive recurring expenses** to not include them in the current budget tracking.

### Technologies used:

This web application was built using **Python**, **Flask** and **Jinja** on the backend, **HTML**, **CSS**, **Javascript**, **Chart.js**, and **Datatables** on the frontend.

**SQLite** was used to store the budget, expenses, and user data in a database.

**Flask-SQLAlchemy** provided an ORM to interact with the SQLite database and **Flask-Login** handled user authentication and sessions.

**Chart.js** and **DataTables** were used to display interactive charts and tables on the frontend to visualize the budget and spending data.


### Overview
``` __init__.py ``` initializes the Flask app and the Flask-SQLAlchemy extension. It registers the blueprints for the application routes and creates the SQLite database.

``` views.py ``` handles the backend logic and routes.

```auth.py``` handles user registration and authentication using Flask-Login.

The ```templates/``` folder holds the Jinja HTML templates rendered by the Flask app that generates the user interface with forms, tables, and charts. //////```layout.html``` holds the general structure of the page ```index.html``` is the homepage with the budget and expenses forms and the data visualization, ```manage.html``` allows creating/editing categories and transactions, and ```archived.html``` shows archived categories and transactions./////////

```static/``` contains CSS stylesheets and JavaScript code.

 ```charts.js``` renders the charts on the homepage. ```tables.js``` initializes Datatables and manages the filtering of the transaction table.

The ``` models.py ``` defines the database models for the Users with their Budget, Expenses. Each user has login credentials, their current budget, and budget timeframe. The expenses are stored in a different table and when they are archived the user budget is stored in the ArchivedInfo table. The Fixed table stored additional information about the recurring expenses. In general, these models allow the app to store and retrieve data from a SQLite database using Flask-SQLAlchemy.

```main.py``` creates and configures the Flask app instance and runs the development web server. The app.run() method starts up the built-in web server for local development and testing when the script is run directly.

### Details

#### Web Page Routes

##### views.py

```views.py``` file handles the routing and rendering of pages.

The ```/``` route renders the ```index.html``` template which displays the homepage which shows a comprehensive view of the user's budget and expenses.

It allows the user to insert a new fixed or variable expense with its details via the ```/add_expense``` route. The route handles POST requests to validate the form data with the ```validate_form_data(form_data)```and inserts the new expense in the Expenses table. It calculates via the ```overbudget()``` function if the new expense makes the total spending exceed the budget and notifies the user if so.

The ```index.html``` page also contains a form to let the user input the budget amount. The budget data with the ```validate_budget_form(form_data)``` from the form is handled by the ```/budget-timeframe``` route which validates the data and adds it to the User table. The route also uses the ```calculate_dates()``` function to calculate when the budget end date will be given a start date and a timeframe. Once the data is added the page displays the total budget amount, the amount spent, and the remaining amount in a doughnut chart. Users can also modify the budget details, such as the amount, through the ```/update_budget``` route.

The page also shows the expenses grouped by categories in a pie chart or bar chart.

The time progression bar chart indicates what day it is relative to the start date and end date of the user budget. Therefore, the user can see how far into their budget period they are.

The line chart in the ```index.html``` page allows the user to visualize their spending over time. The user can choose to view their expenses for the last 2 weeks, 12 months, or 5 years.

The user's recurring expenses are stored in the fixed expenses table and rendered on the index.html page. This allows the user to track their regular bills and subscriptions separately from their variable expenses. It also allows them to generate a new payment for a specific fixed expense via the ```/pay``` route. The route updates the last payment and calculates when the next payment is due.

Finally, the expenses table gives an overview of all the expenses that the user inserted. It allows filtering the expenses by category, date, or search term using JavaScript and the Datatables plugin.
The user can also delete an expense from the table by clicking the delete button which sends a request to the ```/delete``` route to remove the selected expense from the database.

When a user wants to start a new budget, they can archive their current budget and expenses through the ```/archive_expenses``` route. This moves the current budget details and expenses, from the start to the end date of the budget, to the ArchivedInfo table to start tracking a new budget.

Users can also view their archived budgets on the ```/archived``` route which renders the ```archived.html``` template displaying past budgets with their details such as the start and end date, the budget timeframe the budget amount and the total expenses for that budget period. For each archived budget, the user can also see the associated expenses. The ```/delete_archived``` route allows deleting an archived budget and its related expenses from the ArchivedInfo table.

The ```/manage_fixed``` route gets the data from the fixed table for the current users and renders it in the ```fixed.html```page.
The page is comprised of two tables, one table displays the active fixed and one displays the inactive ones. The page allows different operations to edit the fixed expenses.

- The ```/pay ``` handles paying the next installment of a fixed expense.
- The ```/delete_last_payment``` route undoes the last payment of the fixed expense, if there are at least two payments, and recalculates the next payment date, undoing the payment also deletes it from the expenses table.
- The ```/change_amount``` handles the POST request to change the amount of the next payments of the recurring expense.
- The user can also archive a fixed expense through the ```/inactive``` route which moves it to the inactive fixed expenses table.
- Finally, the user can delete the recurring expense and all the associated payment history by clicking the delete button which sends a request to the ```/deletefixed``` route to remove the data from the database.

In the inactive expenses table, the user can view the inactive recurring expenses and can restore their active status by clicking the restore button which sends a request to the ```/active``` route which sets the expense to active again. Therefore it will be displayed in the active fixed expenses table. Or they can permanently delete the inactive fixed expense by clicking the delete button which sends a request to the ```/deletefixed``` route.

##### auth.py

```auth.py``` handles the authentication of users by registering new users and logging them in with the ```login_user```, ```logout_user``` and ```current_user``` functions from Flask-Login.


The ```/login``` route handles logging users in by checking if the email matches any user in the database and, via the ```check_password_hash(hashed_password, password)``` checks if a provided password matches a hashed password. It returns True if the passwords match and False otherwise. If all the credentials are correct, it logs the user in using Flask-Login.

The ```/logout``` route logs the user out.

The  ```/register``` route handles registering new users and inserting them into the Users table if the provided email and password are valid. The password is hashed using the ```generate_password_hash``` function. Finally, it logs the user in.

#### Models
The models.py file defined the SQLAlchemy models for the database. It contains classes for the Users, Budgets, Expenses, FixedExpenses, ArchivedInfo tables.
- The **User** table stores user credentials such as the email, password, and username. It also contains each user budget details such as the budget amount, start and end and end date and the budget timeframe.
- The **Expense** table stores all the expenses inserted by the user with details such as the amount, category, date, and type. It contains an archived column that allows to associate a given expense to a previous budget stored in the ArchivedInfo table.
- The **Fixed** table stores the user's recurring expenses with additional expense details such as the amount, frequency, and next payment date. It also stores the status of a recurring expense, it stores a boolean value which indicates whether the recurring expense payments are currently being paid or if they are not at this moment.
- Finally, the **ArchivedInfo** table stores the archived budgets with their amount, start and end dates, and the timeframe. It also stores the amount of total expenses for that archived budget period. This allows to retrieve previous budgets and their associated expenses.

#### Design Decisions

The program uses Flask-SQLAlchemy query to retrieve data from the database tables and render the data on the frontend templates using Jinja. Using Flask-SQLAlchemy instead of executing raw SQL queries helps with code maintainability and readability, it is also less error-prone since it automatically handles escaping strings among other things. It allows defining models that map to database tables and interacting with records using object-oriented style.

Moreover, the app uses the library Luxon to handle the dates in the budget tracker. Luxon provides a simple API for parsing, validating, manipulating, and formatting dates and times. This was particularly useful with date calculations. For example, calculating the next payment date of a recurring expense based on the last payment date and frequency. It was also useful because it handles time zones.

Having an additional table for the fixed expenses allows for storing additional attributes that are not present in the variable table such as the frequency and next payment date of recurring expenses.

To visualize the data in charts the application uses Chart.js. Chart.js allows for creating different kinds of charts. It is easy to use, but also easy to customize the appearance of the charts.

Finally, DataTables was used to provide the user with pagination, filtering of the table data, and calculating the sum of the expenses column. DataTables is a plugin for jQuery that enhances HTML tables.



#### Further improvements

- Improving the UI of the archived budgets page so that it has charts.

- Allow for better filtering of the expenses for example by only showing a selected time period.

- Add a feature to add budgets for different categories.

- Add a shared budget page where more users can contribute to the same budget. This allows for shared expenses tracking between roommates or family members.

- Automatically add expenses from bank transactions. This removes the need for manual data entry.


#### Sources
 [Python Website Full Tutorial - Flask, Authentication, Databases & More](https://www.youtube.com/watch?v=dam0GPOAvVI&ab_channel=TechWithTim) - Shows how to create an app with Flask

 [DataTables Column Filtering](https://datatables.net/extensions/fixedheader/examples/options/columnFiltering.html) - Shows how to implement column filtering with DataTables

[DataTables Footer Callback](https://datatables.net/examples/advanced_init/footer_callback.html) - Shows how to use a footer callback to display summary information

[Onclick Button Change Chart Type in Chart JS](https://www.youtube.com/watch?v=jZD43r-hw6Q&t=196s&ab_channel=ChartJS) - Demonstrates how to change chart type on button click

[How to Switch Chart to Daily, Weekly and Monthly Data in Chart js](https://www.youtube.com/watch?v=EVHi41f7psQ&ab_channel=ChartJS) - Shows how to change data based on time period selection

Partly inspired by CS50 finance