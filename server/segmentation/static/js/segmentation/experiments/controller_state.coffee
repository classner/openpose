# The different modes the state can be in
Mode =
  draw: 0
  scribble: 1
  edit: 2

# Holds UI state; when something is modified, any dirty items are returned.
# an instance of this is held by ControllerUI
class ControllerState
  constructor: (@ui, @contents, @args) ->
    @loading = true

    @content_index = 0

    # action log and undo/redo
    @undoredo = new UndoRedo(ui, args)
    @log = new ActionLog()
    @log.action($.extend(true, {name:'init'}, args))

    # start with drawing
    @mode = Mode.scribble

    # enabled when shift is held to drag the viewport around
    @panning = false

    # mouse state (w.r.t document page)
    @mousedown = false
    @mousepos = null

    # if true, the user was automagically zoomed in
    # after clicking on a polygon
    @zoomed_adjust = false

    # if nonzero, a modal is visible
    @modal_count = 0

    # buttons
    @btn_draw = if args.btn_draw? then args.btn_draw else '#btn-draw'
    @btn_scribble = if args.btn_scribble? then args.btn_scribble else '#btn-scribble'
    @btn_edit = if args.btn_edit? then args.btn_edit else '#btn-edit'
    @btn_toggle = if args.btn_toggle? then args.btn_toggle else '#btn-toggle'
    @btn_close = if args.btn_close? then args.btn_close else '#btn-close'
    @btn_next = if args.btn_next? then args.btn_next else '#btn-next'
    @btn_prev = if args.btn_prev? then args.btn_prev else '#btn-prev'
    @btn_submit = if args.btn_submit? then args.btn_submit else '#btn-submit'
    @btn_delete = if args.btn_delete? then args.btn_delete else '#btn-delete'
    @btn_zoom_reset = if args.btn_zoom_reset? then args.btn_zoom_reset else '#btn-zoom-reset'

    @closed = ({polys: [], scribbles: []} for i in @contents)
    @open_poly = null
    @sel_poly = null
    @open_scribble = null

    @saved_point = null  # start of drag

    # gui elements
    @stage_ui = new StageUI(@ui, @args)

    @photo_groups = (new StageUIGroup(@stage_ui) for i in @contents)

    @content_index = 0
    @seen_photos = 1

    @init_photo_group()

  next_image: ->
    @photo_groups[@content_index].hide()
    @content_index++
    @photo_groups[@content_index].show()

    if not @photo_groups[@content_index].seen?
      @photo_groups[@content_index].seen = true
      @seen_photos++

      @init_photo_group()

    @update_buttons()

  prev_image: ->
    @photo_groups[@content_index].hide()
    @content_index--
    @photo_groups[@content_index].show()

    @update_buttons()

  init_photo_group: ->
    if @contents[@content_index]?.image?['2048']?
      url = @contents[@content_index].image['2048']

      @set_photo(url)

  segmentation_overlay_url: ->
    @photo_groups[@content_index].segmentation_overlay_url

  set_segmentation_overlay: (url) =>
    @photo_groups[@content_index].set_segmentation_overlay(url, @ui, =>
      @photo_groups[@content_index].segmentation_overlay_url = url
      @loading = false
      @update_buttons()
      console.log "loaded background"
    )

  request_new_segmentation_overlay: =>
    @segmentation_overlay_request.abort() if @segmentation_overlay_request?

    @disable_buttons()
    @loading = true

    @segmentation_overlay_request = $.ajax(
      type: "POST"
      url: window.get_segmentation_url()
      contentType: "application/x-www-form-urlencoded; charset=UTF-8"
      dataType: "text"
      data: @get_scribble_data()
      success: (data, status, jqxhr) =>
        overlay_url = "data:image/jpeg;base64," + data
        @set_segmentation_overlay(overlay_url)
      error: (jqxhr, status, error) ->
        console.log status
      complete: =>
        @segmentation_overlay_request = null
    )

  get_scribble_data: =>
    scribble_list = []
    for scribble in @closed[@content_index].scribbles
      points_scaled = {points: [], is_foreground: scribble.scribble.is_foreground}

      group = @photo_groups[@content_index]

      # calculate the points with respect to a frame with the right aspact ratio
      factor = Math.max(group.size.width, group.size.height)

      x_max = group.size.width / factor
      y_max = group.size.height / factor

      for p in scribble.scribble.points
        points_scaled.points.push([
          Math.max(0, Math.min(x_max, p.x / factor)),
          Math.max(0, Math.min(y_max, p.y / factor)),
        ])
      scribble_list.push(points_scaled)

    results = {}
    photo_id = @contents[@content_index].id
    results[photo_id] = {scribbles: scribble_list}

    version: '1.0'
    results: JSON.stringify(results)

  set_photo: (photo_url) =>
    @disable_buttons()
    @loading = true
    @photo_groups[@content_index].set_photo(photo_url, @ui, =>
      console.log "loaded photo_url: #{photo_url}"
      @request_new_segmentation_overlay()
    )

  # return data that will be submitted
  get_submit_data: =>
    results = {}
    time_ms = {}
    time_active_ms = {}

    for content, index in @contents
      scribble_list = []
      for scribble in @closed[index].scribbles
        points_scaled = {points: [], is_foreground: scribble.scribble.is_foreground}

        group = @photo_groups[index]

        # calculate the points with respect to a frame with the right aspact ratio
        factor = Math.max(group.size.width, group.size.height)

        x_max = group.size.width / factor
        y_max = group.size.height / factor

        for p in scribble.scribble.points
          points_scaled.points.push([
            Math.max(0, Math.min(x_max, p.x / factor)),
            Math.max(0, Math.min(y_max, p.y / factor)),
          ])
        scribble_list.push(points_scaled)

      poly_list = []
      for poly in @closed[index].polys
        points_scaled = []
        for p in poly.poly.points
          points_scaled.push(Math.max(0, Math.min(1,
            p.x / group.size.width)))
          points_scaled.push(Math.max(0, Math.min(1,
            p.y / group.size.height)))
        poly_list.push(points_scaled)

      photo_id = content.id
      results[photo_id] = {}
      results[photo_id].poly = poly_list
      results[photo_id].scribbles = scribble_list
      time_ms[photo_id] = {}
      time_ms[photo_id].poly =
        (p.time_ms for p in @closed[index].polys)
      time_ms[photo_id].scribbles =
        (s.time_ms for s in @closed[index].scribbles)
      time_active_ms[photo_id] = {}
      time_active_ms[photo_id].poly =
        (p.time_active_ms for p in @closed[index].polys)
      time_active_ms[photo_id].scribbles =
        (s.time_active_ms for s in @closed[index].scribbles)

    version: '1.0'
    results: JSON.stringify(results)
    time_ms: JSON.stringify(time_ms)
    time_active_ms: JSON.stringify(time_active_ms)
    action_log: @log.get_submit_data()

  # redraw the stage
  draw: => @photo_groups[@content_index].draw()

  # get mouse position (after taking zoom into account)
  mouse_pos: => @photo_groups[@content_index].mouse_pos()

  # zoom in/out by delta
  zoom_delta: (delta) =>
    @zoomed_adjust = false
    @stage_ui.zoom_delta(delta)
    @update_buttons()
    @update_zoom()

  # reset to 1.0 zoom
  zoom_reset: =>
    @zoomed_adjust = false
    @stage_ui.zoom_reset()
    @update_buttons()
    @update_zoom()

  update_zoom: (redraw=true) =>
    inv_f = 1.0 / @stage_ui.get_zoom_factor()
    for poly in @closed[@content_index].polys
      poly.update_zoom(@ui, inv_f, false)
    for scribble in @closed[@content_index].scribbles
      scribble.update_zoom(@ui, inv_f, false)

    @open_poly?.update_zoom(@ui, inv_f, false)
    @sel_poly?.add_anchors(@ui)
    if redraw
      @draw()

  get_zoom_factor: =>
    @stage_ui.get_zoom_factor()

  translate_delta: (x, y) =>
    @stage_ui.translate_delta(x, y)

  # add a point to the current polygon at point p
  push_point: (p) ->
    @open_poly?.poly.push_point(p)
    @open_poly

  # delete the last point on the open polygon
  pop_point: ->
    @open_poly?.poly.pop_point()
    @open_poly

  # get the location of point i on polygon id
  get_pt: (id, i) ->
    @get_poly(id)?.poly.get_pt(i)

  # start a scribble
  start_scribble: (points, is_foreground) ->
    console.log 'start_scribble'
    console.log points
    console.log is_foreground

    scribble = new Scribble(points, is_foreground)
    @open_scribble = new ScribbleUI(@closed[@content_index].scribbles.length,
      scribble, @stage_ui, @photo_groups[@content_index])
    @open_scribble.timer = new ActiveTimer()
    @open_scribble.timer.start()
    @update_buttons()
    @open_scribble

  create_scribble: ->
    console.log 'create_scribble'

    scribble = @open_scribble
    @open_scribble.time_ms = @open_scribble.timer.time_ms()
    @open_scribble.time_active_ms = @open_scribble.timer.time_active_ms()

    @closed[@content_index].scribbles.push(@open_scribble)
    @open_scribble = null

    scribble

  remove_scribble: ->
    scribble = @closed[@content_index].scribbles.pop()

    scribble.remove_all()
    null

  insert_scribble: (points, is_foreground, id, time_ms, time_active_ms) ->
    scribble = new Scribble(points, is_foreground)
    scribble_ui = new ScribbleUI(id, scribble, @stage_ui,
      @photo_groups[@content_index])
    scribble_ui.time_ms = time_ms
    scribble_ui.time_active_ms = time_active_ms
    @closed[@content_index].scribbles.splice(id, 0, scribble_ui)
    @update_buttons()
    scribble_ui

  # add an open polygon using points
  create_poly: (points) ->
    console.log 'create_poly:'
    console.log points
    @open_poly.remove_all() if @open_poly?
    poly = new Polygon(points)
    @open_poly = new PolygonUI(@closed[@content_index].polys.length, poly,
      @stage_ui, @photo_groups[@content_index])
    @open_poly.timer = new ActiveTimer()
    @open_poly.timer.start()
    @update_buttons()
    @open_poly

  # add a closed polygon in the specified slot
  insert_closed_poly: (points, id, time_ms, time_active_ms) ->
    poly = new Polygon(points)
    poly.close()
    closed_poly = new PolygonUI(id, poly, @stage_ui,
      @photo_groups[@content_index])
    closed_poly.time_ms = time_ms
    closed_poly.time_active_ms = time_active_ms
    @closed[@content_index].polys.splice(id, 0, closed_poly)
    @update_buttons()
    closed_poly

  # return polygon id
  get_poly: (id) ->
    for p in @closed[@content_index].polys
      if p.id == id
        return p
    return null

  # return number of polygons
  num_polys: -> @closed[@content_index].polys.length

  # delete the open polygon
  remove_open_poly: ->
    @open_poly?.remove_all()
    @open_poly = null

  # close the open polygon
  close_poly: ->
    if @open_poly?
      @open_poly.time_ms = @open_poly.timer.time_ms()
      @open_poly.time_active_ms = @open_poly.timer.time_active_ms()
      poly = @open_poly
      @open_poly.poly.close()
      @closed[@content_index].polys.push(@open_poly)
      @open_poly = null
      @update_buttons()
      poly
    else
      null

  can_close: =>
    if not @loading and @open_poly?
      if (window.min_vertices? and @open_poly.poly.num_points() < window.min_vertices)
        return false
      @open_poly.poly.can_close()
    else
      false

  # re-open the most recently closed polygon
  unclose_poly: ->
    if @mode == Mode.draw and not @open_poly? and @num_polys() > 0
      @open_poly = @closed[@content_index].polys.pop()
      @open_poly.poly.unclose()
      @update_buttons()
      @open_poly
    else
      null

  # true if the selected polygon can be deleted
  can_delete_sel: ->
    not @loading and @mode == Mode.edit and @sel_poly? and @num_polys() > 0

  # delete the currently selected polygon
  delete_sel_poly: ->
    if @can_delete_sel()
      for p,i in @closed[@content_index].polys
        if p.id == @sel_poly.id
          @closed[@content_index].polys.splice(i, 1)
          @sel_poly?.remove_all()
          @sel_poly = null
          break
      if @zoomed_adjust then @zoom_reset()
      @update_buttons()
      null
    else
      null

  # select the specified polygon
  select_poly: (ui, id) ->
    if @mode != Mode.edit then return
    if @sel_poly?
      if @sel_poly.id == id then return
      @unselect_poly(false)
    @sel_poly = @get_poly(id)
    @sel_poly.add_anchors(ui)
    @stage_ui.zoom_box(@sel_poly.poly.get_aabb())
    @zoomed_adjust = true
    @update_buttons()
    @update_zoom(false)
    @draw()
    @sel_poly

  unselect_poly: (reset_zoomed_adjust=true) =>
    @sel_poly?.remove_anchors()
    @sel_poly = null
    if reset_zoomed_adjust and @zoomed_adjust
      @zoom_reset()
    @update_buttons()
    null

  abort_action: ->
    switch @mode
      when Mode.draw
        if @open_poly?
          @remove_open_poly()
      when Mode.edit
        if @sel_poly?
          @unselect_poly()
      #when  Mode.scribble
        #do nothing

  switch_mode: (new_mode) ->
    @abort_action()

    @mode = new_mode

    @update_buttons()

  disable_buttons: ->
    set_btn_enabled(@btn_scribble, false)
    set_btn_enabled(@btn_draw, false)
    set_btn_enabled(@btn_edit, false)
    set_btn_enabled(@btn_close, false)
    set_btn_enabled(@btn_toggle, false)
    set_btn_enabled(@btn_next, false)
    set_btn_enabled(@btn_prev, false)
    set_btn_enabled(@btn_submit, false)

  # update cursor only
  update_cursor: ->
    if @panning
      if $.browser.webkit
        if @mousedown
          $('canvas').css('cursor', '-webkit-grabing')
        else
          $('canvas').css('cursor', '-webkit-grab')
      else
        if @mousedown
          $('canvas').css('cursor', '-moz-grabing')
        else
          $('canvas').css('cursor', '-moz-grab')
    else if @mode == Mode.draw
      $('canvas').css('cursor', 'crosshair')
    else if @mode == Mode.scribble
      $('canvas').css('cursor', 'crosshair')
    else
      $('canvas').css('cursor', 'default')

  # update buttons and cursor
  update_buttons: ->
    @update_cursor()

    set_btn_enabled(@btn_submit, not @loading and @seen_photos == @contents.length)
    set_btn_enabled(@btn_draw, not @loading)
    set_btn_enabled(@btn_scribble, not @loading)
    set_btn_enabled(@btn_edit, not @loading)
    set_btn_enabled(@btn_toggle, not @loading)
    set_btn_enabled(@btn_delete, @can_delete_sel())
    set_btn_enabled(@btn_zoom_reset,
      not @loading and @stage_ui.zoom_exp > 0)
    set_btn_enabled(@btn_next,
      not @loading and @content_index < @contents.length - 1)
    set_btn_enabled(@btn_prev,
      not @loading and @content_index > 0)

    switch @mode
      when Mode.draw
        $(@btn_draw).button('toggle')
        set_btn_enabled(@btn_close, @can_close())
      when Mode.scribble
        $(@btn_scribble).button('toggle')
        set_btn_enabled(@btn_close, false)
      when Mode.edit
        $(@btn_edit).button('toggle')
        set_btn_enabled(@btn_close, false)
