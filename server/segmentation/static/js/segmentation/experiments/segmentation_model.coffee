class SegmentationModel
  constructor: (@ui, @view, @args) ->
    # action log and undo/redo
    @undoredo = new UndoRedo(ui, args)
    @log = new ActionLog()
    @log.action($.extend(true, {name:'init'}, args))

  clear: (on_load) ->
    for scribble in @closed[@content_index].scribbles
      scribble.remove_all()
    @closed[@content_index] = {scribbles: []}

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

  next_image: (on_load) ->
    @photo_groups[@content_index].hide()
    @content_index++
    @photo_groups[@content_index].show()

    if not @photo_groups[@content_index].seen?
      @photo_groups[@content_index].seen = true
      @seen_photos++

      @init_photo_group(on_load)
    else
      on_load(false) if on_load?

  prev_image: ->
    @photo_groups[@content_index].hide()
    @content_index--
    @photo_groups[@content_index].show()

  init_photo_group: (on_load) ->
    if @contents[@content_index]?.photo.image?['orig']?
      url = @contents[@content_index].photo.image['orig']

      @set_photo(url, @contents[@content_index]?.bounding_box, on_load)
    else if on_load?
      on_load(false)

  segmentation_overlay_url: ->
    @photo_groups[@content_index].segmentation_overlay_url

  set_segmentation_overlay: (url, on_load) =>
    @photo_groups[@content_index].set_segmentation_overlay(url, @ui, =>
      @photo_groups[@content_index].segmentation_overlay_url = url
      console.log "loaded background"

      on_load?()
    )

  get_scribble_data: =>
    scribble_list = @get_scribble_list(@content_index)

    results = {}
    photo_id = @contents[@content_index].id
    results[photo_id] = {scribbles: scribble_list}

    version: '2.0'
    results: JSON.stringify(results)

  set_photo: (photo_url, bounding_box, on_load) =>
    @photo_groups[@content_index].set_photo(photo_url, bounding_box, @ui, =>
      console.log "loaded photo_url: #{photo_url}"

      group = @photo_groups[@content_index]

      pose = @contents[@content_index]?.parse_pose
      if pose?
        # only take the first pose annotation
        for p in pose[0]
          p_ = group.photo_to_crop({
            x: p[0]
            y: p[1]
          })
          part = new Kinetic.Circle(
            {
              radius: 4
              fill: 'red'
              stroke: 'black'
              strokeWidth: 1
              x: p_.x
              y: p_.y
            }
          )

          @photo_groups[@content_index].add(part)

      if @contents[@content_index]?.scribbles
        scribbles = @contents[@content_index].scribbles

        for scribble in scribbles
          points = (
            group.photo_to_crop({
              x: p[0]
              y: p[1]
            }) for p in scribble.points)

          @start_scribble(points, scribble.is_foreground)
          @create_scribble()?.update(@ui)

      on_load(true) if on_load?
    )

  update: ->
    @open_scribble?.update(@ui)

  get_scribble_list: (index) =>
    scribble_list = []
    for scribble in @closed[index].scribbles
      points_scaled = {points: [], is_foreground: scribble.scribble.is_foreground}

      group = @photo_groups[index]

      max = group.crop_to_photo({
        x: group.size.width
        y: group.size.height
      })

      for p in scribble.scribble.points
        p_ = group.crop_to_photo(p)
        points_scaled.points.push([
          Math.max(0, Math.min(max.x, p_.x)),
          Math.max(0, Math.min(max.y, p_.y)),
        ])
      scribble_list.push(points_scaled)

    return scribble_list

  # return data that will be submitted
  get_submit_data: =>
    results = {}
    time_ms = {}
    time_active_ms = {}

    for content, index in @contents
      scribble_list = @get_scribble_list(index)


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

