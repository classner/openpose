# Main control logic for the UI.  Actions in this class delegate through
# undo/redo and check whether something is feasible.
class SegmentationController
  constructor: (contents, args) ->
    @s = new SegmentationModel(@, contents, args)

    # disable right click
    $(document).on('contextmenu', (e) =>
      @click(e)
      false
    )

    # capture all clicks and disable text selection
    $(document)
      .on('click', @click)
      .on('mousedown', @mousedown)
      .on('mouseup', @mouseup)
      .on('mousemove', @mousemove)
      .on('selectstart', -> false)

    # init buttons
    #$(@s.btn_draw).on('click', =>
      #if @s.mode != Mode.draw then @switch_mode(Mode.draw))
    #$(@s.btn_scribble).on('click', =>
      #if @s.mode != Mode.scribble then @switch_mode(Mode.scribble))
    $(@s.btn_toggle).on('click', =>
      if @s.mode == Mode.scribble
        @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
    )
    #$(@s.btn_edit).on('click', =>
      #if @s.mode != Mode.edit then @switch_mode(Mode.edit))
    #$(@s.btn_close).on('click', =>
      #if not @s.loading then @close_poly())
    #$(@s.btn_delete).on('click', =>
      #if not @s.loading then @delete_sel_poly())
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
      #when 68 # D
        #if @s.mode != Mode.draw then @switch_mode(Mode.draw)
        #false
      #when 65 # A
        #if @s.mode != Mode.edit then @switch_mode(Mode.edit)
        #false
      #when 83 # S
        #if @s.mode != Mode.scribble then @switch_mode(Mode.scribble)
        #false
      when 84 # T
        if @s.mode == Mode.scribble
          @s.photo_groups[@s.content_index].toggle_segment_layer()?.draw()
        false
      when 46,8 # delete,backspace
        switch @s.mode
          when Mode.draw
            @remove_open_poly()
          when Mode.edit
            @delete_sel_poly()
        false
      when 27 # esc
        switch @s.mode
          when Mode.draw
            @s.zoom_reset()
          when Mode.edit
            @unselect_poly()
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

  click: (e) =>
    if @s.panning then return
    p = @s.mouse_pos()
    if not p? then return
    if not @s.loading and @s.mode == Mode.draw
      if e.button > 1
        @close_poly()
      else
        if @s.open_poly?
          ue = new UEPushPoint(p)
          if @s.open_poly.poly.can_push_point(p)
            @s.undoredo.run(ue)
          else
            @s.log.attempted(ue.entry())
        else
          @s.undoredo.run(new UECreatePolygon(
            @s.mouse_pos()))
        @s.stage_ui.translate_mouse_click()

  mousedown: (e) =>
    if @s.modal_count > 0 then return true
    @s.mousedown = true
    @s.mousepos = {x: e.pageX, y: e.pageY}
    @s.update_cursor()

    p = @s.mouse_pos()
    if p? and not @s.loading and not @s.panning and @s.mode == Mode.scribble
      #if e.button == 1 # left mouse buttons
      is_foreground = e.which == 1
      @s.start_scribble([@s.mouse_pos()], is_foreground)

    return not @s.panning

  mouseup: (e) =>
    @s.mousedown = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()

    if not @s.panning and @s.mode == Mode.scribble and @s.open_scribble
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

      if @s.mode == Mode.scribble and @s.open_scribble?
        @s.open_scribble.scribble.push_point(@s.mouse_pos())
        @s.open_scribble.update(@)

    return true

  update: =>
    @s.open_poly?.update(@)
    @s.sel_poly?.update(@)
    @s.open_scribble?.update(@)

  close_poly: => if not @s.loading
    ue = new UEClosePolygon()
    if @s.can_close()
      @s.undoredo.run(ue)
    else
      @s.log.attempted(ue.entry())
      if @s.open_poly?
        pts = @s.open_poly.poly.points
        if pts.length >= 2
          @s.photo_groups[@s.content_index].error_line(pts[0], pts[pts.length - 1])
          @num_failed_closes += 1

      if @num_failed_closes >= 3
        @num_failed_closes = 0
        $('#poly-modal-intersect').modal('show')

  select_poly: (id) =>
    @s.undoredo.run(new UESelectPolygon(id))

  unselect_poly: =>
    if @s.mode == Mode.edit
      @s.undoredo.run(new UEUnselectPolygon())

  remove_open_poly: (id) =>
    @s.undoredo.run(new UERemoveOpenPoly())

  delete_sel_poly: =>
    ue = new UEDeletePolygon()
    if @s.can_delete_sel()
      @s.undoredo.run(ue)
    else
      @s.log.attempted(ue.entry())

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

  switch_mode: (mode) =>
    @s.undoredo.run(new UEToggleMode(mode))
