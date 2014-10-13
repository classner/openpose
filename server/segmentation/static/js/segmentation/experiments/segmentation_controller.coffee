# Main control logic for the UI.  Actions in this class delegate through
# undo/redo and check whether something is feasible.
class SegmentationController
  constructor: (contents, args) ->
    @s = new SegmentationModel(@, contents, args)

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

    # init buttons
    $(@s.btn_toggle).on('click', =>
      @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
    )
    $(@s.btn_zoom_reset).on('click', =>
      if not @s.loading then @zoom_reset())
    $(@s.btn_next).on('click', =>
      if not @s.loading then @next_image())
    $(@s.btn_prev).on('click', =>
      if not @s.loading then @prev_image())

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
      @s.modal_count += 1
      true
    )
    $('.modal').on('hide', =>
      @s.modal_count -= 1
      true
    )

    # listen for scrolling
    $(window).on('mousewheel DOMMouseScroll', @wheel)

    # listen for translation
    $(window)
      .on('keydown', @keydown)
      .on('keyup', @keyup)
      .on('blur', @blur)

    # keep track of invalid close attempts to show a
    # popup explaining the problem
    @num_failed_closes = 0

  next_image: =>
    @s.undoredo.run(new UENextImage())

  prev_image: =>
    @s.undoredo.run(new UEPrevImage())

  get_submit_data: =>
    @s.get_submit_data()

  keydown: (e) =>
    if @s.modal_count > 0 then return true
    switch e.keyCode
      when 37 # left
        @s.translate_delta(-20, 0)
        false
      when 38 # up
        @s.translate_delta(0, -20)
        false
      when 39 # right
        @s.translate_delta(20, 0)
        false
      when 40 # down
        @s.translate_delta(0, 20)
        false
      when 32 # space
        @s.panning = true
        @s.update_cursor()
        false
      when 84 # T
        @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
        false
      else
        true

  keyup: (e) =>
    @s.panning = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()
    return true

  blur: (e) =>
    @s.panning = false
    @s.mousedown = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()
    return true

  wheel: (e) =>
    if @s.modal_count > 0 then return true
    oe = e.originalEvent
    if oe.wheelDelta?
      @s.zoom_delta(oe.wheelDelta)
    else
      @s.zoom_delta(oe.detail * -60)
    window.scrollTo(0, 0)
    stop_event(e)

  zoom_reset: (e) =>
    @s.zoom_reset()

  mousedown: (e) =>
    if @s.modal_count > 0 then return true
    @s.mousedown = true
    @s.mousepos = {x: e.pageX, y: e.pageY}
    @s.update_cursor()

    p = @s.mouse_pos()
    if p? and not @s.loading and not @s.panning
      #if e.button == 1 # left mouse buttons
      is_foreground = e.which == 1
      @s.start_scribble([@s.mouse_pos()], is_foreground)

    return not @s.panning

  mouseup: (e) =>
    @s.mousedown = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()

    if not @s.panning and @s.open_scribble
      @s.undoredo.run(new UECreateScribble())

    return not @s.panning

  mousemove: (e) =>
    if @s.modal_count > 0 then return true
    if @s.mousedown
      if @s.panning
        scale = 1.0 / @s.stage_ui.get_zoom_factor()
        @s.stage_ui.translate_delta(
          scale * (@s.mousepos.x - e.pageX),
          scale * (@s.mousepos.y - e.pageY),
          false)
        @s.mousepos = {x: e.pageX, y: e.pageY}

      if @s.open_scribble?
        @s.open_scribble.scribble.push_point(@s.mouse_pos())
        @s.open_scribble.update(@)

    return true

  update: =>
    @s.open_scribble?.update(@)

  start_drag_point: (i) =>
    p = @s.sel_poly.poly.get_pt(i)
    @s.drag_valid_point = clone_pt(p)
    @s.drag_start_point = clone_pt(p)

  revert_drag_point: (i) =>
    @s.undoredo.run(new UEDragVertex(i,
      @s.drag_start_point, @s.drag_valid_point))

  progress_drag_point: (i, p) =>
    @s.sel_poly.poly.set_point(i, p)
    if @drag_valid(i) then @s.drag_valid_point = clone_pt(p)

  finish_drag_point: (i, p) =>
    @s.undoredo.run(new UEDragVertex(i, @s.drag_start_point, p))
    @s.drag_valid_point = null
    @s.drag_start_point = null

  drag_valid: (i) =>
    not @s.sel_poly.poly.self_intersects_at_index(i)
