$( ->
  args = {
    'width': $('#mt-container').width() - 4
    'height': $(window).height() - $('#mt-top-nohover').height() - 16
    'container_id': 'mt-container'
    'part_field': 'part-name'
  }

  window.controller_ui = new SegmentPersonTutorial(mt_tut_contents, args)
)
