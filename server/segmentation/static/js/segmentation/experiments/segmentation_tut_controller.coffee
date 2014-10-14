
class SegmentPersonTutorial
  constructor: (@contents, args) ->

    @ui = new SegmentationController(args)

    $('#btn-tut-back').on('click', @btn_back)
    $('#btn-tut-next').on('click', @btn_next)
    $('#btn-submit').on('click', @btn_submit)
    $('#btn-tut-reset').on('click', @btn_reset)

    if @contents.length > 0
      @set_idx(4)

  set_idx: (idx) ->
    @cur_idx = idx
    @content = @contents[idx]
    @ui.view.set_message(@content.message_tut)
    @showing_correct_message = false
    @loading_start()

    next = =>
      @loading_finish()

    if @content.expected_mask_url?
      load_image(@content.expected_mask_url, next)
    else
      next()

  loading_start: =>
    @loading = true
    window.show_modal_loading("Loading...", 250)
    set_btn_enabled('#btn-tut-next', false)
    set_btn_enabled('#btn-tut-reset', false)
    set_btn_enabled('#btn-tut-back', false)
    @set_submit_enabled(false)

  loading_finish: =>
    window.hide_modal_loading()
    @ui.reset(@content.content, ( =>
      set_btn_enabled('#btn-tut-next', true)
      set_btn_enabled('#btn-tut-reset', true)
      set_btn_enabled('#btn-tut-back', @cur_idx > 0)
      @loading = false

      size = @ui.s.photo_groups[@ui.s.content_index].size

      if @content.scribbles?
        for scribble in @content.scribbles
          @ui.s.start_scribble(
            (
              {
                'x': p.x * size.height
                'y': p.y * size.height
              } for p in scribble.points
            ), scribble.is_foreground)
          @ui.s.create_scribble()?.update(@ui)

        @ui.request_new_segmentation_overlay()
    ))

  # check for errors and return whether errors were checked
  check_for_mistakes: () ->
    if @expected_mask
      correct = true

      if correct
        @showing_correct_message = true
        @content.message = @content.message_correct
        @ui.update_ui(@content)
      else
        @content.message = @content.message_error
        @ui.reset_zoom()
        @ui.update_ui(@content)
      return true
    return false

  set_submit_enabled: (b) ->
    if b
      @ui.reset()
      $('#mt-done').show()
      $('#btn-submit').show()
      $('#btn-tut-next').hide()
    else
      $('#mt-done').hide()
      $('#btn-submit').hide()
      $('#btn-tut-next').show()
    set_btn_enabled('#btn-submit', b)
    @submit_enabled = b

  btn_next: =>
    if @showing_correct_message or not @check_for_mistakes()
      if @cur_idx < @contents.length - 1
        @set_idx(@cur_idx + 1)
      else
        @cur_idx += 1
        set_btn_enabled('#btn-next', false)
        set_btn_enabled('#btn-back', true)
        @set_submit_enabled(true)

  btn_back: =>
    if not @loading
      @set_submit_enabled(false)
      if @cur_idx >= 1
        @set_idx(@cur_idx - 1)
