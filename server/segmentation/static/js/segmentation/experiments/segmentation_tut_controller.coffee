
class SegmentPersonTutorial
  constructor: (@contents, args) ->

    @ui = new SegmentationController(args)

    $('#btn-tut-back').on('click', @btn_back)
    $('#btn-tut-next').on('click', @btn_next)
    $('#btn-submit').on('click', @btn_submit)
    $('#btn-tut-reset').on('click', @btn_reset)

    if @contents.length > 0
      @set_idx(0)

  btn_submit: =>
    if @submit_enabled
      window.mt_tutorial_complete()

  set_idx: (idx) ->
    @cur_idx = idx
    @content = @contents[idx]
    @ui.view.set_message(@content.message_tut)
    @showing_correct_message = false
    @loading_start()

    next = =>
      @loading_finish()

    if @content.expected_mask_url?
      load_image(@content.expected_mask_url, (@expected_mask) =>
        @expected_mask_data = @image_data(@expected_mask)

        next()
      )
    else
      @expected_mask = null
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
    ))

  image_data: (img) ->
    canvas = $('<canvas/>')[0]
    canvas.width = img.width
    canvas.height = img.height
    canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height)
    canvas.getContext('2d').getImageData(0, 0, img.width, img.height)

  mask_to_url: (mask) ->
    url_prefix = 'data:image/png;base64,'
    canvas = $('<canvas/>')[0]
    canvas.width = mask.width;
    canvas.height = mask.height;
    canvas.getContext('2d').putImageData(mask, 0, 0)
    url = canvas.toDataURL('image/png')
    url.substring(url_prefix.length, url.length)

  # check for errors and return whether errors were checked
  check_for_mistakes: () ->
    if @expected_mask
      correct = true

      mask_data = @image_data(@ui.s.photo_groups[@ui.s.content_index].overlay_obj)

      error_count = 0
      for i in [0...mask_data.data.length/4 - 1]
        if Math.abs(mask_data.data[4 * i] - @expected_mask_data.data[4 * i]) > 30
          error_count++
          mask_data.data[4 * i + 0] = 255
          mask_data.data[4 * i + 1] = 0
          mask_data.data[4 * i + 2] = 0

      ratio = (error_count / (mask_data.data.length/4 - 1))
      threshold = 0.002
      if @content.threshold?
        threshold = @content.threshold
      correct = ratio < threshold

      if correct
        @showing_correct_message = true
        @ui.view.set_message(@content.message_correct)
      else
        @ui.view.set_message(@content.message_error)
        @ui.s.set_segmentation_overlay(@mask_to_url(mask_data))

      return true
    return false

  set_submit_enabled: (b) ->
    if b
      $('#mt-container').hide()
      $('#mt-done').show()
      $('#btn-submit').show()
      $('#btn-tut-next').hide()
    else
      $('#mt-container').show()
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
        set_btn_enabled('#btn-tut-next', false)
        set_btn_enabled('#btn-tut-back', true)
        @set_submit_enabled(true)

  btn_back: =>
    if not @loading
      @set_submit_enabled(false)
      if @cur_idx >= 1
        @set_idx(@cur_idx - 1)
