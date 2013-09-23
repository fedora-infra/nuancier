var cnter = 0;

function checkboxCheck(checkbox)
{
    theid = checkbox.attr('id');
    $(theid).prop('checked', true);
    checkbox.siblings('label').children('.smallthumb').clone(
        ).attr("id", "sidethumb-"+theid).appendTo($("#sideimages"));
    $("#sidethumb-"+theid).click(function(){
        myid = $(this).attr("id").replace("sidethumb-","");
        $("#"+myid).prop('checked', false);
        $("#fix_info").html($('input[type=checkbox]:checked'
            ).length + " of " + votelimit);
        $("#sidethumb-"+myid).remove();
        $('input[type=checkbox]').prop('disabled', false);
        $(".hoveroverlay").removeClass("limit");
        $(".resizelink").removeClass("limit");
    });
}

$( document ).ready(function() {
    /*There may be some already checked if the user soft refreshes the page
      so this makes sure that they are moved to the sidebar and the count is
      correct*/
    $('input[type=checkbox]:checked').each(function(){checkboxCheck($(this));});
    $("#fix_info").html($('input[type=checkbox]:checked'
        ).length + " of " + votelimit);


    $('input[type=checkbox]').change(function() {
        if ($('input[type=checkbox]:checked').length == votelimit) {
            $('input[type=checkbox]').prop('disabled', true);
            $(".hoveroverlay").addClass("limit");
            $(".resizelink").addClass("limit");
        }
        if($(this).is(':checked')) {
            checkboxCheck($(this));
            if ($('input[type=checkbox]:checked').length == votelimit) {
                $("#fix_info").html($('input[type=checkbox]:checked'
                ).length + " of " + votelimit + " -- You have reached the "
                + "maximum number of votes you can cast.");
            } else {
                $("#fix_info").html($('input[type=checkbox]:checked'
                ).length + " of " + votelimit);
            }
        }
    });
});
