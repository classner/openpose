# Main control logic for the UI.  Actions in this class delegate through
# undo/redo and check whether something is feasible.
class SegmentationController
  constructor: (args) ->
    # gui elements
    @view = new SegmentationView(@ui, args)

    @s = new SegmentationModel(@, @view, args)

    # disable right click
    $(document).on('contextmenu', (e) =>
      false
    )

    # capture all clicks and disable text selection
    $(document)
      .on('mousedown', @mousedown)
      .on('mouseup', @mouseup)
      .on('mousemove', @mousemove)
      .on('selectstart', -> false)

    # buttons
    @btn_toggle = if args.btn_toggle? then args.btn_toggle else '#btn-toggle'
    @btn_clear = if args.btn_clear? then args.btn_clear else '#btn-clear'
    @btn_next = if args.btn_next? then args.btn_next else '#btn-next'
    @btn_prev = if args.btn_prev? then args.btn_prev else '#btn-prev'
    @btn_submit = if args.btn_submit? then args.btn_submit else '#btn-submit'
    @btn_zoom_reset = if args.btn_zoom_reset? then args.btn_zoom_reset else '#btn-zoom-reset'

    # init buttons
    $(@btn_toggle).on('click', =>
      @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
    )
    $(@btn_clear).on('click', =>
      @s.undoredo.run(new UEClearScribbles())
    )
    $(@btn_zoom_reset).on('click', =>
      if not @loading then @zoom_reset())
    $(@btn_next).on('click', =>
      if not @loading then @next_image())
    $(@btn_prev).on('click', =>
      if not @loading then @prev_image())

    # log instruction viewing
    $('#modal-instructions').on('show', =>
      @s.log.action(name: "ShowInstructions")
    )
    $('#modal-instructions').on('hide', =>
      @s.log.action(name: "HideInstructions")
    )

    # keep track of modal state
    # (since we want to allow scrolling)
    $('.modal').on('show', =>
      @modal_count += 1
      true
    )
    $('.modal').on('hide', =>
      @modal_count -= 1
      true
    )

    # listen for scrolling
    $(window).on('mousewheel DOMMouseScroll', @wheel)

    # listen for translation
    $(window)
      .on('keydown', @keydown)
      .on('keyup', @keyup)
      .on('blur', @blur)

  reset: (contents, on_load) ->
    # enabled when shift is held to drag the viewport around
    @panning = false

    # mouse state (w.r.t document page)
    @is_mousedown = false
    @mousepos = null

    # if nonzero, a modal is visible
    @modal_count = 0

    @loading = true
    @disable_buttons()

    @s.reset(contents, (new_image) =>
      if new_image
        @request_new_segmentation_overlay(on_load)
      else
        on_load?()
    )

  next_image: =>
    @loading = true;
    @disable_buttons()

    @s.undoredo.run(new UENextImage((new_image) =>
      if (new_image)
        @request_new_segmentation_overlay()
    ))
    @update_buttons()

  prev_image: =>
    @s.undoredo.run(new UEPrevImage())
    @update_buttons()

  get_submit_data: =>
    @s.get_submit_data()

  keydown: (e) =>
    if @modal_count > 0 then return true
    switch e.keyCode
      when 37 # left
        @translate_delta(-20, 0)
        false
      when 38 # up
        @translate_delta(0, -20)
        false
      when 39 # right
        @translate_delta(20, 0)
        false
      when 40 # down
        @translate_delta(0, 20)
        false
      when 32 # space
        @panning = true
        @update_cursor()
        false
      when 84 # T
        @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
        false
      else
        true

  request_new_segmentation_overlay: (on_load) =>
    @segmentation_overlay_request.abort() if @segmentation_overlay_request?

    @disable_buttons()
    @loading = true

    @segmentation_overlay_request = $.ajax(
      type: "POST"
      url: window.get_segmentation_url()
      contentType: "application/x-www-form-urlencoded; charset=UTF-8"
      dataType: "text"
      data: @s.get_scribble_data()
      success: (data, status, jqxhr) =>
        overlay_url = "data:image/jpeg;base64," + data
        @s.set_segmentation_overlay(overlay_url, =>
          @loading = false
          @update_buttons()
          on_load?()
        )
      error: (jqxhr, status, error) ->
        @loading = false
        console.log status
        on_load?()
      complete: =>
        @segmentation_overlay_request = null
    )

  keyup: (e) =>
    @panning = false
    if @modal_count > 0 then return true
    @update_cursor()
    return true

  blur: (e) =>
    @panning = false
    @is_mousedown = false

    if not @panning and @s.open_scribble
      @s.undoredo.run(new UECreateScribble())

    if @modal_count > 0 then return true
    @update_cursor()

    return true

  wheel: (e) =>
    if @modal_count > 0 then return true
    oe = e.originalEvent
    if oe.wheelDelta?
      @zoom_delta(oe.wheelDelta)
    else
      @zoom_delta(oe.detail * -60)
    window.scrollTo(0, 0)
    stop_event(e)

  mousedown: (e) =>
    if @modal_count > 0 then return true
    @is_mousedown = true
    @mousepos = {x: e.pageX, y: e.pageY}
    @update_cursor()

    p = @s.mouse_pos()
    if p? and not @loading and not @panning
      #if e.button == 1 # left mouse buttons
      is_foreground = e.which == 1
      @s.start_scribble([@s.mouse_pos()], is_foreground)

    return not @panning

  mouseup: (e) =>
    @is_mousedown = false
    if @modal_count > 0 then return true
    @update_cursor()

    if not @panning and @s.open_scribble
      @s.undoredo.run(new UECreateScribble())

    return not @panning

  mousemove: (e) =>
    if @modal_count > 0 then return true
    if @is_mousedown
      if @panning
        scale = 1.0 / @view.get_zoom_factor()
        @translate_delta(
          scale * (@mousepos.x - e.pageX),
          scale * (@mousepos.y - e.pageY),
          false)

        @mousepos = {x: e.pageX, y: e.pageY}
      else
        @s.push_point(@s.mouse_pos())

    return true

  update: =>
    @s.update()

  disable_buttons: ->
    set_btn_enabled(@btn_toggle, false)
    set_btn_enabled(@btn_next, false)
    set_btn_enabled(@btn_prev, false)
    set_btn_enabled(@btn_clear, false)
    set_btn_enabled(@btn_submit, false)

  # update cursor only
  update_cursor: ->
    if @panning
      if $.browser.webkit
        if @is_mousedown
          $('canvas').css('cursor', '-webkit-grabing')
        else
          $('canvas').css('cursor', '-webkit-grab')
      else
        if @is_mousedown
          $('canvas').css('cursor', '-moz-grabing')
        else
          $('canvas').css('cursor', '-moz-grab')
    else
      $('canvas').css('cursor', 'crosshair')

  # update buttons and cursor
  update_buttons: ->
    @update_cursor()

    set_btn_enabled(@btn_submit, not @loading and @s.seen_photos == @s.contents.length)
    set_btn_enabled(@btn_toggle, not @loading)
    set_btn_enabled(@btn_clear, not @loading)
    set_btn_enabled(@btn_zoom_reset,
      not @loading and @view.zoom_exp > 0)
    set_btn_enabled(@btn_next,
      not @loading and @s.content_index < @s.contents.length - 1)
    set_btn_enabled(@btn_prev,
      not @loading and @s.content_index > 0)

  # zoom in/out by delta
  zoom_delta: (delta) =>
    @zoomed_adjust = false
    @view.zoom_delta(delta)
    @update_buttons()
    @update_zoom()

  # reset to 1.0 zoom
  zoom_reset: (e) =>
    @zoomed_adjust = false
    @view.zoom_reset()
    @update_buttons()
    @update_zoom()

  update_zoom: (redraw=true) =>
    inv_f = 1.0 / @get_zoom_factor()
    @s.update_zoom(inv_f, redraw)

  get_zoom_factor: =>
    @view.get_zoom_factor()

  translate_delta: (x, y) =>
    @view.translate_delta(x, y)

