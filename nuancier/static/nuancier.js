var cnter = 0;

function updateSelectionCnt(cb) {
  if (cb.checked){
    cnter += 1;
    $(cb).parent().parent().css('background-color', '#3C6EB4');
  } else {
    cnter -= 1;
    $(cb).parent().parent().css('background-color', '#FFF');
  }
  
  var popup = document.getElementById('fix_info');
  popup.innerHTML = cnter + ' pictures selected';
  popup.className = "large_button";
}
