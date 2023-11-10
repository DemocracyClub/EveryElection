"use strict"

var NotAThursdayWarning = function (op, date, date_form) {

    var existing_error = date_form.parentNode.querySelector(".ds-error");
    if (existing_error) {
        existing_error.remove();
    }
    if (op === "add") {
        var date_string = date.toLocaleDateString();
        var day_of_the_week = new Intl.DateTimeFormat("en-GB", {weekday: "long"}).format(date);
        var warning = '<div class="ds-error ds-padded" style="clear:both">UK elections are almost always on a Thursday<br>' + date_string + ' is a ' + day_of_the_week + ' not a Thursday. Are you sure that\'s right?</div>';
        date_form.insertAdjacentHTML('afterend', warning);
    }
};

var CheckIsThursday = function (date_form) {
    var day = date_form.querySelector('#id_date-date_0').value;
    var month = date_form.querySelector('#id_date-date_1').value;
    var year = date_form.querySelector('#id_date-date_2').value;

    if (![day, month, year].every(Boolean)) {
        NotAThursdayWarning("remove", date, date_form);
        return;
    }

    var date = new Date([year, month, day]);
    var day_of_week = date.getDay();
    if (day_of_week !== 4) {
        NotAThursdayWarning("add", date, date_form);
    } else {
        NotAThursdayWarning("remove", date, date_form);
    }
};


var date_form = document.getElementById("id_creator_date");
if (date_form != undefined) {
    date_form.querySelectorAll("input").forEach(function (el) {
        el.addEventListener("input", function (el) {
            CheckIsThursday(el.target.parentElement.parentElement);
        });
    });
    CheckIsThursday(date_form.querySelector(".ds-date"));
}


function add_action_button(label, actions) {
    var action_button = document.createElement("button");
    action_button.innerText = label;
    action_button.setAttribute("class", "ds-button");
    action_button.setAttribute("type", "button");

    action_button.addEventListener("click", function () {
        actions.forEach((action) => {
            document.querySelectorAll(action.selector).forEach(function (el) {
                action.action(el);
            });
        });
    });
    return action_button
}

var division_picker = document.getElementById("id_creator_election_organisation_division");
if (division_picker != undefined) {
    // Create a cluster
    var button_div = document.createElement('div');
    button_div.classList.add("ds-cluster")
    button_div.innerHTML = `
          <div>
          </div>
    `;

    // Reset button
    var reset_button = add_action_button("Reset", [
        {
            selector: "input[value=no_seats]",
            action: function (el) {
                el.checked = true;
            }
        },
        {
            selector: "input[name$='-seats_contested']",
            action: function (el) {
                el.value = "";
            }
        },
    ]);
    button_div.querySelector("div").insertAdjacentElement("beforeend", reset_button);

    // All up button


    // Scheduled button
    var scheduled_button = add_action_button("Scheduled", [
        {
            selector: "input[value=seats_contested]",
            action: function (el) {
                el.checked = true;
            }
        },
        {
            selector: "input[name$='-seats_contested']",
            action: function (el) {
                el.value = 1;
            }
        },
    ]);
    button_div.querySelector("div").insertAdjacentElement("beforeend", scheduled_button);

    var all_up_botton = add_action_button("All up", [
        {
            selector: "input[value=seats_contested]",
            action: function (el) {
                el.checked = true;
            }
        },
        {
            selector: "input[name$='-seats_contested']",
            action: function (el) {
                el.value = el.getAttribute("max");
            }
        }
    ]);
    button_div.querySelector("div").insertAdjacentElement("beforeend", all_up_botton);

    division_picker.insertAdjacentElement("beforebegin", button_div);

}
