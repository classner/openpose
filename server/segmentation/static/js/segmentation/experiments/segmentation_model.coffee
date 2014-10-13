class SegmentationModel
  constructor: (@ui, @view, @args) ->
    # action log and undo/redo
    @undoredo = new UndoRedo(ui, args)
    @log = new ActionLog()
    @log.action($.extend(true, {name:'init'}, args))

  reset: (@contents, on_load) ->
    @closed = ({scribbles: []} for i in @contents)
    @open_scribble = null

    @saved_point = null  # start of drag

    if @photo_groups?
      for group in @photo_groups
        group.destroy()

      @photo_groups = null

    @photo_groups = (new SegmentationViewGroup(@view) for i in @contents)

    @content_index = 0
    @seen_photos = 1

    @init_photo_group(on_load)

  push_point: (p) ->
    if @open_scribble
      @open_scribble.scribble.push_point(p)
      @open_scribble.update(@ui)

  next_image: ->
    @photo_groups[@content_index].hide()
    @content_index++
    @photo_groups[@content_index].show()

    if not @photo_groups[@content_index].seen?
      @photo_groups[@content_index].seen = true
      @seen_photos++

      @init_photo_group()

  prev_image: ->
    @photo_groups[@content_index].hide()
    @content_index--
    @photo_groups[@content_index].show()

  init_photo_group: (on_load) ->
    if @contents[@content_index]?.image?['2048']?
      url = @contents[@content_index].image['2048']

      @set_photo(url, on_load)
    else if on_load?
      on_load()

  segmentation_overlay_url: ->
    @photo_groups[@content_index].segmentation_overlay_url

  set_segmentation_overlay: (url, on_load) =>
    @photo_groups[@content_index].set_segmentation_overlay(url, @ui, =>
      @photo_groups[@content_index].segmentation_overlay_url = url
      console.log "loaded background"

      on_load() if on_load?
    )

  get_scribble_data: =>
    scribble_list = @get_scribble_list()

    results = {}
    photo_id = @contents[@content_index].id
    results[photo_id] = {scribbles: scribble_list}

    version: '2.0'
    results: JSON.stringify(results)

  set_photo: (photo_url, on_load) =>
    @photo_groups[@content_index].set_photo(photo_url, @ui, =>
      console.log "loaded photo_url: #{photo_url}"
      on_load() if on_load?
    )

  update: ->
    @open_scribble?.update(@ui)

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

  # start a scribble
  start_scribble: (points, is_foreground) ->
    console.log 'start_scribble'
    console.log points
    console.log is_foreground

    scribble = new Scribble(points, is_foreground)
    @open_scribble = new ScribbleUI(@closed[@content_index].scribbles.length,
      scribble, @view, @photo_groups[@content_index])
    @open_scribble.timer = new ActiveTimer()
    @open_scribble.timer.start()
    @open_scribble

  create_scribble: ->
    console.log 'create_scribble'

    scribble = @open_scribble
    @open_scribble.time_ms = @open_scribble.timer.time_ms()
    @open_scribble.time_active_ms = @open_scribble.timer.time_active_ms()

    @closed[@content_index].scribbles.push(@open_scribble)
    @open_scribble = null

    scribble

  update_zoom: (inv_f, redraw) ->
    for scribble in @closed[@content_index].scribbles
      scribble.update_zoom(@ui, inv_f, false)

    if redraw
      @draw()

  remove_scribble: ->
    scribble = @closed[@content_index].scribbles.pop()

    scribble.remove_all()
    null

  insert_scribble: (points, is_foreground, id, time_ms, time_active_ms) ->
    scribble = new Scribble(points, is_foreground)
    scribble_ui = new ScribbleUI(id, scribble, @view,
      @photo_groups[@content_index])
    scribble_ui.time_ms = time_ms
    scribble_ui.time_active_ms = time_active_ms
    @closed[@content_index].scribbles.splice(id, 0, scribble_ui)
    scribble_ui

