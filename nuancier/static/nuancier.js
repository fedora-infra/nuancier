var cnter = 0;

function updateSelectionCnt(cb) {
  if (cb.checked){
    cnter += 1;
  } else {
    cnter -= 1;
  }
  
  var popup = document.getElementById('fix_info');
  popup.innerHTML = cnter + ' pictures selected';
  popup.className = "large_button";
}
