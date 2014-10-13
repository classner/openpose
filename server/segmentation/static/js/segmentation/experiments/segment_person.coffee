$( ->
  args = {
    'width': $('#mt-container').width() - 4
    'height': $(window).height() - $('#mt-top-nohover').height() - 16
    'container_id': 'mt-container'
  }

  window.controller_ui = new SegmentationController(args)
  window.controller_ui.reset(window.mt_contents)
)

btn_submit = ->
  window.mt_submit(window.controller_ui.get_submit_data)

# wait for everything to load before allowing submit
$(window).on('load', ->
  $('#btn-submit').on('click', btn_submit)
)
