// Set the current date as default for the date inputs
document.addEventListener('DOMContentLoaded', function() {
    let dates = document.getElementsByName('date')
    dates.forEach(element => {
        element.value = (new Date().toISOString().slice(0, 10))
    });
})

// Add an expired class if the date payment of each fixed expense is past the current date
document.addEventListener('DOMContentLoaded', function() {
    let payDate = document.querySelectorAll(".pay");
    payDate.forEach(element => {
        if (element.querySelector(".renew").innerText < new Date().toISOString().slice(0, 10)) {
            element.querySelector("button[type='submit']").classList.add("btn-expired")
        }
    });
})

// Show or hide input for 'other' category in the 'add expense' form
// https://stackoverflow.com/questions/16015933/how-can-i-show-a-hidden-div-when-a-select-option-is-selected
function showOther(divId, element) {
    const input = document.getElementById(divId).querySelector("input[type='text']");

    document.getElementById(divId).style.display = element.value == "Other" ? 'block' : 'none';
    // add a required attribute if the block is displayed
    if (document.getElementById(divId).style.display == "block") {
        input.setAttribute('required', '');
        document.getElementById("category_div").classList.remove("col-6");
        document.getElementById("category_div").classList.add("col-3");

    } else {
        input.removeAttribute('required');
        document.getElementById("category_div").classList.add("col-6");
        document.getElementById("category_div").classList.remove("col-3");
    };
}

// Show or hide input to add a timeframe for the recurring expenses in the 'add expense' form
function showTimeframe(divId, element) {
    const input = document.getElementById('selectTimeframe');
    document.getElementById(divId).style.display = element.value == "Fixed" ? 'flex' : 'none';
    if (document.getElementById(divId).style.display == "flex") {
        input.setAttribute('required', '');
    } else {
        input.removeAttribute('required');
    };

}

// Show or hide input for custom timeframe in the 'add expense' form for the fixed expenses
function showCustom(divId, element) {

    const inputs = document.getElementById(divId).querySelectorAll(".timeframe");
    document.getElementById(divId).style.display = element.value == "Custom" ? 'flex' : 'none';

    for (const input of inputs) {
        if (document.getElementById(divId).style.display == "flex") {
            input.setAttribute('required', '');
        } else {
            input.removeAttribute('required');
        };
    }
}


// Shows the data of the timechart forward or backwards in time
function showData(mover) {
    const startScale = dataChart.config.options.scales.x.min;
    const endScale = dataChart.config.options.scales.x.max;
    document.getElementById('previous').disabled = false;
    document.getElementById('next').disabled = false;
    const firstDate = first_day;
    const lastDate = last_day;
    console.log("first = " + firstDate);
    console.log("last = " + lastDate);

    // If the left arrow is clicked previous data in time is shown
    if (mover.value == "previous") {

        // Displays the data from the previous 7 days by changing the min and max date shown on the x axis
        if (dataChart.config.data.datasets[0].data == week) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).minus({
                days: 7
            }).toISODate();
            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).minus({
                days: 7
            }).toISODate();
        }

        // Displays the data from the previous 6 months
        if (dataChart.config.data.datasets[0].data == month) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).minus({
                month: 6
            }).toISODate();
            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).minus({
                month: 6
            }).toISODate();
        }

        // Displays the data from the previous 2 years
        if (dataChart.config.data.datasets[0].data == year) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).minus({
                year: 2
            }).toISODate();
            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).minus({
                year: 2
            }).toISODate();

        }
        // Disables the left arrow button when the earliest data is shown
        if (dataChart.config.options.scales.x.min <= firstDate) {
            document.getElementById('previous').disabled = true;
        }
        dataChart.update();
    }

    // If the right arrow is clicked following data in time is shown

    if (mover.value == "next") {
        // Displays the data from the next 7 days

        if (dataChart.config.data.datasets[0].data == week) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).plus({
                days: 7
            }).toISODate();
            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).plus({
                days: 7
            }).toISODate();

        }

        // Displays the data from the next 6 months
        if (dataChart.config.data.datasets[0].data == month) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).plus({
                month: 6
            }).toISODate();
            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).plus({
                month: 6
            }).toISODate();
        }

        // Displays the data from the next 2 years
        if (dataChart.config.data.datasets[0].data == year) {
            dataChart.config.options.scales.x.min = DateTime.fromISO(startScale).plus({
                year: 2
            }).toISODate();

            dataChart.config.options.scales.x.max = DateTime.fromISO(endScale).plus({
                year: 2
            }).toISODate();
        }
        // Disables the right arrow button when the latest data is shown
        if (dataChart.config.options.scales.x.max >= lastDate) {
            document.getElementById('next').disabled = true;
        }
        dataChart.update();
    }
}



// Changes the time unit in which the time chart is displayed
function timeFrame(period, timeunit, number) {
    // Show the data a in a span of 15 days
    if (period.value == 'day') {
        time = { days: number };
    }
    // Show the data in a span of 12 months
    else if (period.value == 'month') {
        time = { months: number };
    }

    // Show the data in a span of 5 years
    else if (period.value == 'year') {
        time = { years: number };
    }

    dataChart.config.options.scales.x.time.unit = period.value;
    dataChart.config.data.datasets[0].data = timeunit;
    dataChart.config.options.scales.x.min =
        DateTime.now().minus(time).toISODate();
    dataChart.config.options.scales.x.max = DateTime.now().toISODate();

    dataChart.update();
}


// Toggles the category chart betwee pie and bar chart views
function changeChart() {
    // Destroy chart if it exists already
    const catChart = document.getElementById('categoryChart');
    if (categoryChart) {
        categoryChart.destroy();
    }

    // Create new chart based on current config type
    if (categoryChart.config.type === 'pie') {
        categoryChart = new Chart(catChart, configBar);
        document.getElementById('categoryChartbtn').innerHTML = '<i class="fa-solid fa-chart-pie"></i>  Show as pie chart ';
    } else if (categoryChart.config.type === 'bar') {
        categoryChart = new Chart(catChart, configPie);
        document.getElementById('categoryChartbtn').innerHTML = '<i class="fa-regular fa-chart-bar"></i>  Show as bar chart';
    }
}


// Bootstrap form validation
document.addEventListener('DOMContentLoaded', function() {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
        .forEach(function(form) {
            form.addEventListener('submit', function(event) {

                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }

                form.classList.add('was-validated')
            }, false)
        })
})()
