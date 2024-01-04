from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Expense, Fixed, User, ArchivedInfo
from . import db

# from sqlalchemy import select
from sqlalchemy import update, func

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import add, sub

views = Blueprint("views", __name__)


# Gets the data from the database to display it in the main page
@views.route("/", methods=["GET"])
@login_required
def index():
    if request.method == "GET":
        # Get information for the current user from the database
        budget = (
            User.query.filter_by(id=current_user.id)
            .with_entities(
                User.username,
                User.budget,
                User.budget_start,
                User.budget_end,
                User.budget_time,
            )
            .first()
        )
        budget_start = budget.budget_start or 0
        budget_end = budget.budget_end or 0

        # Calculate the sum of the expenses in the budget period
        expenses_sum = (
            Expense.query.filter_by(user_id=current_user.id)
            .filter(
                Expense.archived == 0,
                Expense.date <= budget_end,
                Expense.date >= budget_start,
            )
            .with_entities(func.sum(Expense.amount))
            .scalar()
        )
        expenses_sum = expenses_sum or 0

        # Get the list of all the expenses
        current_expenses = (
            Expense.query.filter_by(user_id=current_user.id)
            .filter(Expense.archived == 0)
            .order_by(Expense.date.desc())
            .all()
        )

        # Get the fixed expenses and their details
        fixed = (
            db.session.query(
                Expense.description,
                Fixed.id,
                Fixed.fixed_amount,
                Fixed.timeframe,
                Fixed.renewal_date,
                func.count(Expense.id).label("count"),
            )
            .join(Expense, Expense.fixed_id == Fixed.id)
            .filter(Fixed.user_id == current_user.id, Fixed.status == 1)
            .group_by(Fixed.id)
            .order_by(Fixed.renewal_date)
            .all()
        )

        percentages = {}

        if expenses_sum != 0:
            for type in ["Fixed", "Variable"]:
                sum_type = sum(
                    [
                        expense.amount
                        for expense in current_expenses
                        if expense.type == type
                        and expense.archived == 0
                        and expense.date <= budget_end
                        and expense.date >= budget_start
                    ]
                )
                percent_type = round(sum_type / expenses_sum * 100)
                percentages[type] = percent_type

        # Get the expenses in the current budget divided by categories with their amount
        categories = (
            Expense.query.filter_by(user_id=current_user.id)
            .filter(
                Expense.archived == 0,
                Expense.date <= budget_end,
                Expense.date >= budget_start,
            )
            .with_entities(
                Expense.category, (func.sum(Expense.amount).label("total_amount"))
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .all()
        )

        # Get all the categories from the database
        all_categories = (
            Expense.query.filter_by(user_id=current_user.id)
            .with_entities(Expense.category)
            .distinct()
            .all()
        )

        # Get the expenses grouped by different time periods
        amount_by_date = (
            Expense.query.filter_by(user_id=current_user.id)
            .with_entities(
                Expense.date.label("day"), func.sum(Expense.amount).label("day_sum")
            )
            .group_by(Expense.date)
            .order_by(Expense.date)
            .all()
        )

        amount_by_month = (
            Expense.query.filter_by(user_id=current_user.id)
            .with_entities(
                func.strftime("%Y-%m", Expense.date).label("month"),
                func.sum(Expense.amount).label("month_sum"),
            )
            .group_by(func.strftime("%Y-%m", Expense.date))
            .order_by(Expense.date)
            .all()
        )

        amount_by_year = (
            Expense.query.filter_by(user_id=current_user.id)
            .with_entities(
                func.strftime("%Y", Expense.date).label("year"),
                func.sum(Expense.amount).label("year_sum"),
            )
            .group_by(func.strftime("%Y", Expense.date))
            .order_by(Expense.date)
            .all()
        )

        return render_template(
            "index.html",
            budget=budget,
            expenses_sum=expenses_sum,
            categories=categories,
            all_categories=all_categories,
            current_expenses=current_expenses,
            amount_by_date=amount_by_date,
            amount_by_month=amount_by_month,
            amount_by_year=amount_by_year,
            fixed=fixed,
            percentages=percentages,
        )


# Add a new expense from the database
@views.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    if request.method == "POST":
        # Validate form data from the new expense form
        not_valid_data = validate_form_data(request.form)
        if not_valid_data:
            return redirect(url_for("views.index"))
        else:
            new_fixed_id = None
            category = request.form.get("category")
            date = request.form.get("date")
            amount = request.form.get("amount")
            type = request.form.get("type")

            # Handle Other category
            if category == "Other":
                category = (
                    request.form.get("other_category").strip().lower().capitalize()
                )

            # Handle new fixed expense
            if type == "Fixed":
                # Get custom timeframe if selected
                if request.form.get("fixed_div") == "Custom":
                    timeframe_number = request.form.get("timeframe_number")
                    timeframe_unit = request.form.get("timeframe_unit")
                    timeframe = f"{timeframe_number} {timeframe_unit}"
                else:
                    timeframe = request.form.get("fixed_div")

                # Calculate next payment date based on timeframe
                next_payment = calculate_dates(date, timeframe, add)[0]

                # Add a new recurring expense in the fixed table
                new_fixed = Fixed(
                    timeframe=timeframe,
                    fixed_amount=amount,
                    user_id=current_user.id,
                    renewal_date=next_payment,
                    last_payment=date,
                )
                db.session.add(new_fixed)
                db.session.commit()
                new_fixed_id = new_fixed.id

            # Add the first payment of the recurring expense to the expenses table too
            new_expense = Expense(
                description=request.form.get("description")
                .strip()
                .lower()
                .capitalize(),
                amount=amount,
                category=category,
                date=date,
                type=type,
                fixed_id=new_fixed_id,
                user_id=current_user.id,
            )
            db.session.add(new_expense)
            db.session.commit()

            flash("Expense added!", category="success")

            if overbudget():
                flash("You went over your budget", category="error")

        return redirect(url_for("views.index"))


# Add a new budget
@views.route("/add_budget", methods=["POST"])
@login_required
def add_budget():
    if request.method == "POST":
        # Validate the data from the form
        not_valid_data = validate_budget_form(request.form)

        if not_valid_data:
            return redirect(url_for("views.index"))
        # Get the data from the form
        amount = request.form.get("amount")
        timeframe_number = request.form.get("timeframe_number")
        timeframe_unit = request.form.get("timeframe_unit")
        date = request.form.get("date")
        timeframe = f"{timeframe_number} {timeframe_unit}"
        budget_end = calculate_dates(date, timeframe, add)[0]

        # Update the database with the new budget information
        db.session.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                budget=amount,
                budget_start=date,
                budget_end=budget_end,
                budget_time=timeframe,
            )
        )

        db.session.commit()

        return redirect(url_for("views.index"))


# Update budget detail
@views.route("/update_budget", methods=["POST"])
@login_required
def update_budget():
    if request.method == "POST":
        amount = request.form.get("amount")
        if amount:
            # Validate amount
            try:
                amount = float(amount)
            except ValueError:
                flash("Input a valid number to modify the budget", category="error")
                return redirect(url_for("views.index"))

            # Check if amount is too large
            if float(amount) < 999999999999999.9999:
                db.session.execute(
                    update(User).where(User.id == current_user.id).values(budget=amount)
                )
            else:
                flash("Budget amount too large", category="error")

        timeframe_number = request.form.get("timeframe_number")
        timeframe_unit = request.form.get("timeframe_unit")
        if timeframe_number and timeframe_unit:
            # Validate timeframe number
            if (
                float(timeframe_number) > 999999999999999.9999
                or float(timeframe_number) < 1
            ):
                flash("Invalid timeframe number", category="error")
                return redirect(url_for("views.index"))

            # Validate timeframe unit
            if timeframe_unit not in ["days", "weeks", "months", "years"]:
                flash("Choose a valid time unit", category="error")
                return redirect(url_for("views.index"))

            # Build timeframe string
            timeframe = f"{timeframe_number} {timeframe_unit}"

        else:
            # Use existing timeframe
            timeframe = User.query.get(current_user.id).budget_time

        # Validate date
        if request.form.get("budget-date"):
            date = request.form.get("budget-date")
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                flash("Select a valid date", category="error")
                return redirect(url_for("views.index"))
        else:
            # Use existing start date
            date = User.query.get(current_user.id).budget_start

        # Calculate end date
        budget_end = calculate_dates(date, timeframe, add)[0]

        # Update database
        db.session.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(budget_start=date, budget_end=budget_end, budget_time=timeframe)
        )
        db.session.commit()

        return redirect(url_for("views.index"))


# Pays the next instalment of the selected fixed expense and adds the new payment to the expenses table
@views.route("/pay", methods=["POST"])
@login_required
def pay():
    if request.method == "POST":
        id = request.form.get("id")
        if id:
            fixed = Fixed.query.get(id)
            if fixed:
                # Get the expense detail
                expense = (
                    Expense.query.filter_by(user_id=current_user.id, fixed_id=id)
                    .with_entities(Expense.description, Expense.category, Expense.type)
                    .first()
                )
                if not expense:
                    flash("Cannot pay this recurring expense", category="error")
                    return redirect(request.referrer)
                # Calculate new payment date
                last_payment, next_payment = calculate_dates(
                    fixed.last_payment, fixed.timeframe, add
                )

                # Add new payment to database
                new_expense = Expense(
                    description=expense.description,
                    amount=fixed.fixed_amount,
                    category=expense.category,
                    date=last_payment,
                    type=expense.type,
                    user_id=current_user.id,
                    fixed_id=fixed.id,
                )
                db.session.add(new_expense)

                # Update fixed expense in database
                db.session.execute(
                    update(Fixed)
                    .where(Fixed.id == id, Fixed.user_id == current_user.id)
                    .values(last_payment=last_payment, renewal_date=next_payment)
                )
                db.session.commit()
                flash(
                    f"Recurring expense {new_expense.description} paid.",
                    category="success",
                )

                # Check if user went over budget
                if overbudget():
                    flash("You went over your budget", category="error")

        return redirect(request.referrer)


# Moves the expenses of the current budget to the archive and starts a new budget
@views.route("/archive_expenses", methods=["POST"])
@login_required
def archive_expenses():
    if request.method == "POST":
        information = User.query.get(current_user.id)
        # Check information exists
        if not information:
            flash("User information not found", category="error")
            return redirect(url_for("views.index"))

        # Check budget start and end dates exist
        if not information.budget_end or not information.budget_start:
            flash(
                "Add a budget start date and end date before archiving expenses",
                category="error",
            )
            return redirect(url_for("views.index"))

        # Get the expenses of the current budget to be archived
        current_expenses = (
            Expense.query.filter_by(user_id=current_user.id)
            .filter(Expense.archived == 0)
            .filter(Expense.date <= information.budget_end)
            .filter(Expense.date >= information.budget_start)
            .all()
        )

        if not current_expenses:
            flash("No expenses found for current budget", category="error")
            return redirect(url_for("views.index"))

        # Calculate total of the expenses to archive
        total = (
            db.session.query(func.sum(Expense.amount))
            .filter(Expense.user_id == current_user.id)
            .filter(Expense.archived == 0)
            .filter(Expense.date <= information.budget_end)
            .filter(Expense.date >= information.budget_start)
            .scalar()
        )

        # Create archived budget record
        new_info = ArchivedInfo(
            budget=information.budget,
            budget_start=information.budget_start,
            budget_end=information.budget_end,
            budget_time=information.budget_time,
            total=total,
            user_id=current_user.id,
        )
        db.session.add(new_info)
        db.session.commit()

        # Update expenses status to archived
        db.session.execute(
            update(Expense)
            .where(
                Expense.user_id == current_user.id,
                Expense.archived == 0,
                Expense.date <= information.budget_end,
                Expense.date >= information.budget_start,
            )
            .values(archived=new_info.id)
        )
        db.session.commit()

        # Reset current budget details
        db.session.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(budget=0, budget_time=0, budget_start=None, budget_end=None)
        )
        db.session.commit()

        return redirect(url_for("views.index"))


# Deletes an expense from the database. If the expense is the last one associated with a fixed subscription, the subscription is also deleted.
@views.route("/delete_expense", methods=["POST"])
@login_required
def delete_expense():
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            # Get the expense to be deleted
            expense = Expense.query.get(id)

            if expense:
                # If expense type is 'Fixed', gets all its associated expenses.
                if expense.type == "Fixed":
                    expenses = Expense.query.filter_by(
                        user_id=current_user.id, type="Fixed", fixed_id=expense.fixed_id
                    ).all()

                    # If only 1 associated expense exists, deletes the fixed record.
                    if len(expenses) <= 1:
                        fixed = Fixed.query.get(expense.fixed_id)
                        if fixed:
                            db.session.delete(fixed)
            db.session.delete(expense)
            db.session.commit()
            flash("Expense deleted", category="success")
        return redirect(url_for("views.index"))


# Undoes the last payment for a recurring expense and recalculates the next payment date
@views.route("/delete_last_payment", methods=["POST"])
@login_required
def delete_last_payment():
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            fixed = Fixed.query.get(id)

            if fixed:
                # Calculate new last payment date and next payment date
                new_last_date, new_next_payment = calculate_dates(
                    fixed.last_payment, fixed.timeframe, sub
                )

                # Get expense to delete with matching fixed id and last payment date
                expense_delete = (
                    Expense.query.filter_by(
                        user_id=current_user.id, fixed_id=id, date=fixed.last_payment
                    )
                    .order_by(Expense.date.desc())
                    .first()
                )

                # Get all expenses for this fixed subscription
                allexpense_fixed = (
                    Expense.query.filter_by(user_id=current_user.id, fixed_id=id)
                    .order_by(Expense.date.desc())
                    .all()
                )

                if len(allexpense_fixed) <= 1:
                    flash("You can't delete the last payment", category="error")
                else:
                    # Update fixed subscription with new dates
                    db.session.execute(
                        update(Fixed)
                        .where(Fixed.id == id, Fixed.user_id == current_user.id)
                        .values(
                            last_payment=new_last_date, renewal_date=new_next_payment
                        )
                    )
                    if expense_delete:
                        db.session.delete(expense_delete)
                        flash("Expense deleted", category="success")
                    db.session.commit()

    return redirect(url_for("views.manage"))


# Delete a recurring expense with all its associated payments
@views.route("/delete_fixed", methods=["POST"])
@login_required
def delete_fixed():
    if request.method == "POST":
        id = request.form.get("id")
        if id:
            fixed = Fixed.query.get(id)
            # Get all the expenses with the fixed_id of the recurring expense to be deleted
            all_expenses = Expense.query.filter_by(
                user_id=current_user.id, fixed_id=id
            ).all()
            if all_expenses:
                for expense in all_expenses:
                    db.session.delete(expense)
                db.session.delete(fixed)
                db.session.commit()
                flash(
                    f"All expenses of {all_expenses[0].description} have been deleted",
                    category="success",
                )
    return redirect(url_for("views.manage"))


# Deletes an archived budget record and associated expenses from the database
@views.route("/delete_archived", methods=["POST"])
@login_required
def delete_archived():
    if request.method == "POST":
        id = request.form.get("id")
        # Get the archived info to delete
        archived_info = ArchivedInfo.query.filter_by(id=id).first()
        if archived_info:
            db.session.delete(archived_info)

        # Get all the expenses associated with the archived info
        expenses = Expense.query.filter_by(user_id=current_user.id, archived=id).all()
        if expenses:
            # For each expense check if it is the last expense for a recurring expense, if so delete the fixed record as well
            for expense in expenses:
                if (
                    expense.type == "Fixed"
                    and len(
                        Expense.query.filter_by(
                            user_id=current_user.id, fixed_id=expense.fixed_id
                        ).all()
                    )
                    <= 1
                ):
                    fixed = Fixed.query.get(expense.fixed_id)
                    if fixed:
                        db.session.delete(fixed)
                db.session.delete(expense)
        db.session.commit()
        flash("Archived budget and associated expenses deleted", category="success")

    return redirect(url_for("views.archived"))


# Makes a fixed expense inactive and updates its status in the database
@views.route("/inactive", methods=["POST"])
@login_required
def inactive():
    if request.method == "POST":
        id = request.form.get("id")
        if id:
            fixed = Fixed.query.get(id)
            if fixed:
                db.session.execute(
                    update(Fixed)
                    .where(Fixed.id == id, Fixed.user_id == current_user.id)
                    .values(status=False)
                )
                db.session.commit()

        return redirect(url_for("views.manage"))


# Restores the status of a fixed expense to active
@views.route("/active", methods=["POST"])
@login_required
def active():
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            # Updates the status of the fixed expense in the table
            db.session.execute(
                update(Fixed)
                .where(Fixed.id == id, Fixed.user_id == current_user.id)
                .values(status=True)
            )
            db.session.commit()

    return redirect(url_for("views.manage"))


# Updates the amount of a fixed expense in the database
@views.route("/change_amount", methods=["POST"])
@login_required
def change_amount():
    if request.method == "POST":
        id = request.form.get("id")
        amount = request.form.get("amount")
        # If the id and amount are provided, update the fixed amount
        if id and amount:
            db.session.execute(
                update(Fixed)
                .where(Fixed.user_id == current_user.id, Fixed.id == id)
                .values(fixed_amount=amount)
            )
            db.session.commit()
        else:
            flash("Cannot change the amount", category="error")

        return redirect(url_for("views.manage"))


# Gets the fixed expenses and their details form the database
@views.route("/manage_fixed", methods=["GET"])
@login_required
def manage():
    fixed = (
        db.session.query(
            Expense.description,
            Fixed.id,
            Expense.amount,
            Fixed.fixed_amount,
            Expense.category,
            Expense.date,
            Fixed.timeframe,
            Fixed.renewal_date,
            Fixed.last_payment,
            Fixed.status,
            Expense.fixed_id,
            func.count(Expense.id).label("count"),
        )
        .join(Expense, Expense.fixed_id == Fixed.id)
        .filter(Fixed.user_id == current_user.id)
        .group_by(Fixed.id)
        .order_by(Fixed.renewal_date)
        .all()
    )

    return render_template("manage.html", fixed=fixed, user=current_user)


# Gets the data from archived budgets
@views.route("/archived", methods=["GET"])
@login_required
def archived():
    # Get all old budgets
    archived_info = (
        ArchivedInfo.query.filter_by(user_id=current_user.id)
        .order_by(ArchivedInfo.id.desc())
        .all()
    )
    # Get archived expenses
    archived_expenses = (
        Expense.query.filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc())
        .all()
    )
    # Calculate the total amount spent for each budget
    totals = (
        Expense.query.filter_by(user_id=current_user.id)
        .with_entities(func.sum(Expense.amount).label("total_amount_spent"))
        .group_by(Expense.archived)
        .all()
    )

    return render_template(
        "archived.html",
        user=current_user,
        archived_info=archived_info,
        archived_expenses=archived_expenses,
        totals=totals,
    )


# Validate the form data before adding a new expense to the databse
def validate_form_data(form_data):
    errors = []
    p = re.compile(r"\d+(\.\d+)?$")

    if not form_data.get("description"):
        errors.append("Add a valid expense description")
    elif len(form_data.get("description")) > 30:
        errors.append(
            f'Description cannot be longer than 30 characters. It is currently {len(form_data.get("description"))} characters.'
        )

    # Check if the amount input is valid
    if form_data.get("amount"):
        try:
            float(form_data.get("amount"))
        except ValueError:
            errors.append("Insert a valid amount number")
        if float(form_data.get("amount")) > 999999999999999.9999:
            errors.append("Amount number too large")
    else:
        errors.append("Expense amount cannot be left blank")

    # Validate the category input
    if not form_data.get("category"):
        errors.append("Select a valid category")
    elif form_data.get("category") == "Other":
        # Check if other category is valid
        category = form_data.get("other_category").strip().lower().capitalize()
        if not category:
            errors.append("Write a new category or choose an existing one")
        elif len(form_data.get("other_category")) > 30:
            errors.append(
                f'Category cannot be longer than 30 characters. It is currently {len(form_data.get("other_category"))} characters.'
            )
        # Check if 'other' category is already present
        all_categories = (
            Expense.query.filter_by(user_id=current_user.id)
            .with_entities(Expense.category)
            .distinct()
            .all()
        )
        if all_categories:
            list_categories = list(zip(*all_categories))[0]
            if category in list_categories:
                errors.append(
                    "Category already present, select it from the dropdown list"
                )

    # Check if the date is valid
    if not form_data.get("date"):
        errors.append("Select a date")
    try:
        datetime.strptime(form_data.get("date"), "%Y-%m-%d")
    except ValueError:
        errors.append("Select a valid date")

    # Validate expense type
    if not form_data.get("type"):
        errors.append("Select a valid type")

    # Validate the data for a new recurring expense
    elif form_data.get("type") == "Fixed":
        if not form_data.get("fixed_div"):
            errors.append("Select a timeframe")
        # Validate custom timeframe
        if form_data.get("fixed_div") == "Custom":
            if not form_data.get("timeframe_number") or not form_data.get(
                "timeframe_unit"
            ):
                errors.append("Please enter a valid timeframe number and unit")
            try:
                int(form_data.get("timeframe_number"))
            except ValueError:
                errors.append("Insert a valid number")
            if float(form_data.get("amount")) > 999999999999999.9999:
                errors.append("Amount number too large")
            if form_data.get("timeframe_unit") not in [
                "days",
                "weeks",
                "months",
                "years",
            ]:
                errors.append("Choose a valid time unit")

    for error_msg in errors:
        flash(error_msg, category="error")
        return errors


# Validate the budget data
def validate_budget_form(form_data):
    errors = []

    # Check if the amount input is valid
    if form_data.get("amount"):
        try:
            float(form_data.get("amount"))
        except ValueError:
            errors.append("Insert a valid budget amount")
        if float(form_data.get("amount")) > 999999999999999.9999:
            errors.append("Budget amount too large")
    else:
        errors.append("Add a valid budget amount")

    # Validate date
    if not form_data.get("date"):
        errors.append("Select a date")
    try:
        datetime.strptime(form_data.get("date"), "%Y-%m-%d")
    except ValueError:
        errors.append("Select a valid date")

    # Validate timeframe
    if not form_data.get("timeframe_number") or not form_data.get("timeframe_unit"):
        errors.append("Select a valid timeframe")
    try:
        int(form_data.get("timeframe_number"))
    except ValueError:
        errors.append("Insert a valid number")
    if (
        float(form_data.get("timeframe_number")) > 999999999999999.9999
        or float(form_data.get("timeframe_number")) < 1
    ):
        errors.append("Invalid timeframe number")
    if form_data.get("timeframe_unit") not in ["days", "weeks", "months", "years"]:
        errors.append("Choose a valid time unit")

    for error_msg in errors:
        flash(error_msg, category="error")
        return errors


# Add or substract time from a date
def calculate_dates(previous_date, timeframe, op):
    # Parse the previous date
    previous_date_obj = datetime.strptime(previous_date, "%Y-%m-%d")

    # Get the timefrfame in a dictionary
    timeframe_list = timeframe.split()
    timeframe_dict = {timeframe_list[1]: int(timeframe_list[0])}

    # Calculate new dates based on timeframe and operator and convert them to strings
    new_last_payment_obj = op(previous_date_obj, relativedelta(**timeframe_dict))
    new_last_payment = new_last_payment_obj.strftime("%Y-%m-%d")
    next_payment = (new_last_payment_obj + relativedelta(**timeframe_dict)).strftime(
        "%Y-%m-%d"
    )

    return new_last_payment, next_payment


# Checks if a user went overbudget
def overbudget():
    # Get the user budget details
    user = (
        User.query.filter_by(id=current_user.id)
        .with_entities(User.budget_start, User.budget_end, User.budget)
        .first()
    )

    budget_start = user.budget_start or 0
    budget_end = user.budget_end or 0

    # Get the sum of the expenses within the budget timeframe
    expenses_sum = (
        Expense.query.filter_by(user_id=current_user.id)
        .filter(
            Expense.archived == 0,
            Expense.date <= budget_end,
            Expense.date >= budget_start,
        )
        .with_entities(func.sum(Expense.amount))
        .scalar()
    )
    expenses_sum = expenses_sum or 0

    if expenses_sum > float(user.budget):
        return True
    else:
        return False