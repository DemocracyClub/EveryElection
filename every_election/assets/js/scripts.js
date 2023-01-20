"use strict"

var NotAThursdayWarning = function(op, date, date_form) {

    var existing_error = date_form.parentNode.querySelector(".ds-error");
    if(existing_error) {
        existing_error.remove();
    }
    if (op === "add") {
        var date_string = date.format("mmmm dS yyyy");
        var day_of_the_week = date.format("dddd");
        var warning = '<div class="ds-error ds-padded" style="clear:both">UK elections are almost always on a Thursday<br>'+date_string+' is a '+ day_of_the_week +' not a Thursday. Are you sure that\'s right?</div>';
        date_form.insertAdjacentHTML('afterend', warning);
    }
};

var CheckIsThursday = function (date_form) {
    var day = date_form.querySelector('#id_date-date_0').value;
    var month = date_form.querySelector('#id_date-date_1').value;
    var year = date_form.querySelector('#id_date-date_2').value;

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
    date_form.addEventListener("change", function (el) {
        CheckIsThursday(el.target.parentElement.parentElement);
    });
    CheckIsThursday(date_form.querySelector(".ds-date"));
}


var division_picker = document.getElementById("id_creator_election_organisation_division");
if (division_picker != undefined) {

    var all_contested_button = document.createElement("button");
    all_contested_button.innerText = "Mark all seats as contested (can't be undone)";
    all_contested_button.setAttribute("class", "ds-button");
    all_contested_button.setAttribute("type", "button");

    all_contested_button.addEventListener("click", function() {
        document.querySelectorAll("input").forEach(function (el) {
            if (el.value === "seats_contested") {
                el.checked = 1;
            }
        })
    });
    division_picker.insertAdjacentElement("beforebegin", all_contested_button);
}
