# Control encapsulated into UndoableEvent objects
class UEToggleMode extends UndoableEvent
  constructor: (@mode) ->
    @open_points = null
    @sel_poly_id = null
    @sel_mode = null

  run: (ui) ->
    @sel_mode = ui.s.mode

    switch @sel_mode
      when Mode.draw
        if ui.s.open_poly?
          @open_points = ui.s.open_poly.poly.clone_points()
      when Mode.edit
        @sel_poly_id = ui.s.sel_poly?.id

    ui.s.switch_mode(@mode)
    ui.s.update_buttons()

  redo: (ui) ->
    ui.s.switch_mode(@mode)
    ui.s.update_buttons()

  undo: (ui) ->
    ui.s.switch_mode(@sel_mode)

    switch @sel_mode
      when Mode.draw
        if @open_points?
          ui.s.create_poly(@open_points)?.update(ui)
      when Mode.edit
        if @sel_poly_id?
          ui.s.select_poly(ui, @sel_poly_id)?.update(ui)

  entry: -> { name: "UEToggleMode", args: { mode: @mode } }

class UERemoveOpenPoly extends UndoableEvent
  constructor: ->
    @open_points = null

  run: (ui) ->
    if ui.s.open_poly?
      @open_points = ui.s.open_poly.poly.clone_points()
    ui.s.remove_open_poly()
    ui.s.update_buttons()

  redo: (ui) ->
    ui.s.remove_open_poly()
    ui.s.update_buttons()

  undo: (ui) ->
    if @open_points?
      ui.s.create_poly(@open_points)?.update(ui)

  entry: -> { name: "UERemoveOpenPoly" }

class UEPushPoint extends UndoableEvent
  constructor: (p) -> @p = clone_pt(p)
  run: (ui) -> ui.s.push_point(@p)?.update(ui)
  undo: (ui) -> ui.s.pop_point()?.update(ui)
  entry: -> { name: "UEPushPoint", args: { p: @p } }

class UECreatePolygon extends UndoableEvent
  constructor: (p) -> @p = clone_pt(p)
  run: (ui) -> ui.s.create_poly([@p])?.update(ui)
  undo: (ui) -> ui.s.remove_open_poly()?.update(ui)
  entry: -> { name: "UECreatePolygon", args: { p: @p } }

class UECreateScribble extends UndoableEvent
  run: (ui) ->
    ui.s.create_scribble()?.update(ui)

    # in case we are currently waiting for a overlay to arrive, abort the
    # request
    ui.s.segmentation_overlay_request.abort() if ui.segmentation_overlay_request?

    if ui.s.segmentation_overlay_url?
      @old_overlay_url = ui.s.segmentation_overlay_url
    else
      @old_overlay_url = null

    ui.s.request_new_segmentation_overlay()

  undo: (ui) ->
    [..., scribble_ui] = ui.s.closed_scribbles
    @points = scribble_ui.scribble.clone_points()
    @is_foreground = scribble_ui.scribble.is_foreground
    @id = scribble_ui.id
    @time_ms = scribble_ui.time_ms
    @time_active_ms = scribble_ui.time_active_ms
    ui.s.remove_scribble()

    @overlay_url = ui.s.segmentation_overlay_url
    ui.set_segmentation_overlay(@old_overlay_url)
  redo: (ui) ->
    ui.s.insert_scribble(@points, @is_foreground, @id, @time_ms, @time_active_ms)?.update(ui)

    ui.set_segmentation_overlay(@overlay_url)
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
    for p,i in ui.s.closed_polys
      p.id = i
      p.update(ui)
  undo: (ui) ->
    ui.s.insert_closed_poly(@points, @sel_poly_id,
      @time_ms, @time_active_ms)
    for p,i in ui.s.closed_polys
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
