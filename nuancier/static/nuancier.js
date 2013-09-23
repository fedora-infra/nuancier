function checkboxCheck(checkbox) {
    theid = checkbox.attr('id');
    $(theid).attr('checked', true);

    if ($('input[type=checkbox]:checked').length > votelimit) {
        document.getElementById(theid).checked = false;
        return;
    }

    checkbox.siblings('label').children('.smallthumb').clone(
        ).attr("id", "sidethumb-"+theid).appendTo($("#sideimages"));

    $("#sidethumb-"+theid).click(function(){
        myid = $(this).attr("id").replace("sidethumb-","");
        $("#"+myid).attr('checked', false);
        $("#fix_info").html($('input[type=checkbox]:checked'
            ).length + " of " + votelimit);
        $("#sidethumb-"+myid).remove();
        $(".hoveroverlay").removeClass("limit");
        $(".resizelink").removeClass("limit");
    });
}


function updateActionAndInfo(){
    if ($('input[type=checkbox]:checked').length == votelimit) {
        $(".hoveroverlay").addClass("limit");
        $(".resizelink").addClass("limit");

        $("#fix_info").html($('input[type=checkbox]:checked'
        ).length + " of " + votelimit + " -- You have reached the "
        + "maximum number of votes you can cast.");
    } else {
        $("#fix_info").html($('input[type=checkbox]:checked'
        ).length + " of " + votelimit);
    }
}


$( document ).ready(function() {
    /*There may be some already checked if the user soft refreshes the page
      so this makes sure that they are moved to the sidebar and the count is
      correct*/
    $('input[type=checkbox]:checked').each(function(){checkboxCheck($(this));});
    updateActionAndInfo();

    $('input[type=checkbox]').change(function() {
        if($(this).is(':checked')) {
            checkboxCheck($(this));
            updateActionAndInfo();
        }
    });
});
