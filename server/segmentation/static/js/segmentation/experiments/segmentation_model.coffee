class SegmentationModel
  constructor: (@ui, @contents, @args) ->
    @loading = true

    # action log and undo/redo
    @undoredo = new UndoRedo(ui, args)
    @log = new ActionLog()
    @log.action($.extend(true, {name:'init'}, args))

    # enabled when shift is held to drag the viewport around
    @panning = false

    # mouse state (w.r.t document page)
    @mousedown = false
    @mousepos = null

    # if nonzero, a modal is visible
    @modal_count = 0

    # buttons
    @btn_toggle = if args.btn_toggle? then args.btn_toggle else '#btn-toggle'
    @btn_next = if args.btn_next? then args.btn_next else '#btn-next'
    @btn_prev = if args.btn_prev? then args.btn_prev else '#btn-prev'
    @btn_submit = if args.btn_submit? then args.btn_submit else '#btn-submit'
    @btn_zoom_reset = if args.btn_zoom_reset? then args.btn_zoom_reset else '#btn-zoom-reset'

    # gui elements
    @stage_ui = new SegmentationView(@ui, @args)

    @reset(@contents)

  reset: (@contents) ->
    @closed = ({scribbles: []} for i in @contents)
    @open_scribble = null

    @saved_point = null  # start of drag

    if @photo_groups?
      for group in @photo_groups
        group.destroy()

      @photo_groups = null

    @photo_groups = (new SegmentationViewGroup(@stage_ui) for i in @contents)

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
    scribble_list = @get_scribble_list()

    results = {}
    photo_id = @contents[@content_index].id
    results[photo_id] = {scribbles: scribble_list}

    version: '2.0'
    results: JSON.stringify(results)

  set_photo: (photo_url) =>
    @disable_buttons()
    @loading = true
    @photo_groups[@content_index].set_photo(photo_url, @ui, =>
      console.log "loaded photo_url: #{photo_url}"
      @request_new_segmentation_overlay()
    )

  get_scribble_list: =>
    scribble_list = []
    for scribble in @closed[@content_index].scribbles
      points_scaled = {points: [], is_foreground: scribble.scribble.is_foreground}

      group = @photo_groups[@content_index]

      # calculate the points with respect to a frame with the right aspact ratio
      factor = group.size.height

      x_max = group.size.width / factor
      y_max = group.size.height / factor

      for p in scribble.scribble.points
        points_scaled.points.push([
          Math.max(0, Math.min(x_max, p.x / factor)),
          Math.max(0, Math.min(y_max, p.y / factor)),
        ])
      scribble_list.push(points_scaled)

    return scribble_list

  # return data that will be submitted
  get_submit_data: =>
    results = {}
    time_ms = {}
    time_active_ms = {}

    for content, index in @contents
      scribble_list = @get_scribble_list()


      photo_id = content.id
      results[photo_id] = {}
      results[photo_id].scribbles = scribble_list
      time_ms[photo_id] = {}
      time_ms[photo_id].scribbles =
        (s.time_ms for s in @closed[index].scribbles)
      time_active_ms[photo_id] = {}
      time_active_ms[photo_id].scribbles =
        (s.time_active_ms for s in @closed[index].scribbles)

    version: '2.0'
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
    for scribble in @closed[@content_index].scribbles
      scribble.update_zoom(@ui, inv_f, false)

    if redraw
      @draw()

  get_zoom_factor: =>
    @stage_ui.get_zoom_factor()

  translate_delta: (x, y) =>
    @stage_ui.translate_delta(x, y)

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

  disable_buttons: ->
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
    else
      $('canvas').css('cursor', 'crosshair')

  # update buttons and cursor
  update_buttons: ->
    @update_cursor()

    set_btn_enabled(@btn_submit, not @loading and @seen_photos == @contents.length)
    set_btn_enabled(@btn_toggle, not @loading)
    set_btn_enabled(@btn_zoom_reset,
      not @loading and @stage_ui.zoom_exp > 0)
    set_btn_enabled(@btn_next,
      not @loading and @content_index < @contents.length - 1)
    set_btn_enabled(@btn_prev,
      not @loading and @content_index > 0)
