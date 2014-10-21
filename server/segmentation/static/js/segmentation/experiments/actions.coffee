class UENextImage extends UndoableEvent
  constructor: (@on_load) ->
  run: (ui) -> ui.s.next_image(@on_load)
  undo: (ui) -> ui.s.prev_image()
  entry: -> { name: "UENextImage" }

class UEPrevImage extends UndoableEvent
  run: (ui) -> ui.s.prev_image()
  undo: (ui) -> ui.s.next_image()
  entry: -> { name: "UEPrevImage" }

class UEClearScribbles extends UndoableEvent
  run: (ui) ->
    @closed = ui.s.closed[ui.s.content_index]
    ui.s.clear()
    @old_overlay_url = ui.s.segmentation_overlay_url()
    ui.request_new_segmentation_overlay()
  undo: (ui) ->
    ui.s.closed[ui.s.content_index] = @closed
    for scribble in ui.s.closed[ui.s.content_index].scribbles
      scribble.add_line()

    @overlay_url = ui.s.segmentation_overlay_url()
    ui.s.set_segmentation_overlay(@old_overlay_url)
  redo: (ui) ->
    @closed = ui.s.closed[ui.s.content_index]
    ui.s.clear()
    ui.s.set_segmentation_overlay(@overlay_url)
  entry: -> { name: "UEClearScribbles" }

class UECreateScribble extends UndoableEvent
  run: (ui) ->
    ui.s.create_scribble()?.update(ui)

    # in case we are currently waiting for a overlay to arrive, abort the
    # request
    ui.s.segmentation_overlay_request.abort() if ui.segmentation_overlay_request?

    @old_overlay_url = ui.s.segmentation_overlay_url()

    ui.request_new_segmentation_overlay()

  undo: (ui) ->
    [..., scribble_ui] = ui.s.closed[ui.s.content_index].scribbles
    @points = scribble_ui.scribble.clone_points()
    @is_foreground = scribble_ui.scribble.is_foreground
    @id = scribble_ui.id
    @time_ms = scribble_ui.time_ms
    @time_active_ms = scribble_ui.time_active_ms
    ui.s.remove_scribble()

    @overlay_url = ui.s.segmentation_overlay_url()
    ui.s.set_segmentation_overlay(@old_overlay_url)
  redo: (ui) ->
    ui.s.insert_scribble(@points, @is_foreground, @id, @time_ms, @time_active_ms)?.update(ui)

    ui.s.set_segmentation_overlay(@overlay_url)
  entry: -> { name: "UECreateScribble", args: { pts: @pts } }

class UEClosePolygon extends UndoableEvent
  run: (ui) -> ui.s.close_poly()?.update(ui)
  undo: (ui) -> ui.s.unclose_poly()?.update(ui)
  entry: -> { name: "UEClosePolygon" }

class UESelectPolygon extends UndoableEvent
  constructor: (@id) ->
  run: (ui) ->
    @sel_poly_id = ui.s.sel_poly?.id
    ui.s.select_poly(ui, @id)
  undo: (ui) ->
    if @sel_poly_id?
      ui.s.select_poly(ui, @sel_poly_id)
    else
      ui.s.unselect_poly()
  redo: (ui) ->
    ui.s.select_poly(ui, @id)
  entry: -> { name: "UESelectPolygon", args: { id: @id } }

class UEUnselectPolygon extends UndoableEvent
  constructor: () ->
  run: (ui) ->
    @sel_poly_id = ui.s.sel_poly?.id
    ui.s.unselect_poly()
  undo: (ui) ->
    if @sel_poly_id?
      ui.s.select_poly(ui, @sel_poly_id)
  redo: (ui) ->
    ui.s.unselect_poly()
  entry: -> { name: "UEUnselectPolygon" }

class UEDeletePolygon extends UndoableEvent
  run: (ui) ->
    @points = ui.s.sel_poly.poly.clone_points()
    @time_ms = ui.s.sel_poly.time_ms
    @time_active_ms = ui.s.sel_poly.time_active_ms
    @sel_poly_id = ui.s.sel_poly.id
    ui.s.delete_sel_poly()
    for p,i in ui.s.closed[ui.s.content_index].polys
      p.id = i
      p.update(ui)
  undo: (ui) ->
    ui.s.insert_closed_poly(@points, @sel_poly_id,
      @time_ms, @time_active_ms)
    for p,i in ui.s.closed[ui.s.content_index].polys
      p.id = i
      p.update(ui)
    ui.s.select_poly(ui, @sel_poly_id)
  entry: -> { name: "UEDeletePolygon" }

class UEDragVertex extends UndoableEvent
  constructor: (@i, p0, p1) ->
    @p0 = clone_pt(p0)
    @p1 = clone_pt(p1)
  run: (ui) ->
    sp = ui.s.sel_poly
    sp.poly.set_point(@i, @p1)
    sp.anchors[@i].setPosition(@p1.x, @p1.y)
    sp.update(ui)
  undo: (ui) ->
    sp = ui.s.sel_poly
    sp.poly.set_point(@i, @p0)
    sp.anchors[@i].setPosition(@p0.x, @p0.y)
    sp.update(ui)
  entry: -> { name: "UEDragVertex", args: { i: @i, p0: @p0, p1: @p1 } }
