# Wrapper for Kinetic.Stae
class StageUI
  constructor: (ui, args) ->
    # maximum possible size
    @bbox = {width: args.width, height: args.height}
    # actual size
    @size = {width: args.width, height: args.height}

    # zoom information
    @origin = {x: 0, y: 0}
    @zoom_exp = 0
    @zoom_exp_max = 7

    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @size.width,
      height: @size.height)
    @photo_layer = new Kinetic.Layer()
    @stage.add(@photo_layer)
    @photo_layer.setZIndex(0)
    @overlay_layer = new Kinetic.Layer()
    @stage.add(@overlay_layer)
    @overlay_layer.setZIndex(1)
    @object_layer = new Kinetic.Layer()
    @stage.add(@object_layer)
    @object_layer.setZIndex(2)

    @overlay_layer_visible = true

    @stage.on('mouseout', => @object_layer.draw())
    @stage.on('mousemove', ->
      if not ui.s.panning
        ui.update()
    )

  toggle_segment_layer: ->
    @overlay_layer_visible = !@overlay_layer_visible

    if @overlay_layer_visible
      @overlay_layer.show()
    else
      @overlay_layer.hide()

    @overlay_layer

  add: (o, opacity=1.0, duration=0.4) ->
    @add_to_layer(o, @object_layer, opacity, duration)

  add_to_layer: (o, layer, opacity=1.0, duration=0.4) ->
    layer.add(o)
    if duration > 0
      o.setOpacity(0)
      o.add_trans = o.transitionTo(opacity:opacity, duration:duration)
    else
      o.setOpacity(opacity)

  remove: (o, duration=0.4) -> if o?
    o.add_trans?.stop()
    if duration > 0
      o.removing = true
      o.transitionTo(
        opacity: 0
        duration: duration
        callback: do (o) -> -> o.remove()
      )
    else
      o.remove()

  draw: ->
    @photo_layer.draw()
    @overlay_layer.draw()
    @object_layer.draw()

  mouse_pos: ->
    p = @stage.getMousePosition()
    if not p?
      p
    else
      scale = Math.pow(2, -@zoom_exp)
      x: Math.min(Math.max(0, p.x * scale + @origin.x), @size.width)
      y: Math.min(Math.max(0, p.y * scale + @origin.y), @size.height)

  zoom_reset: (redraw=true) ->
    @zoom_exp = 0
    @origin = {x: 0, y: 0}
    @stage.setOffset(@origin.x, @origin.y)
    @stage.setScale(1.0)
    if redraw
      @stage.draw()

  # zoom in/out by delta (in log_2 units)
  zoom_delta: (delta, p=@stage.getMousePosition()) ->
    if delta?
      @zoom_set(@zoom_exp + delta * 0.001, p)

  get_zoom_factor: ->
    Math.pow(2, @zoom_exp)

  # set the zoom level (in log_2 units)
  zoom_set: (new_zoom_exp, p=@stage.getMousePosition()) ->
    if @k_loading? or not new_zoom_exp? or not p? then return
    old_scale = Math.pow(2, @zoom_exp)
    @zoom_exp = Math.min(@zoom_exp_max, new_zoom_exp)
    if @zoom_exp <= 0
      @zoom_reset()
    else
      new_scale = Math.pow(2, @zoom_exp)
      f = (1.0 / old_scale - 1.0 / new_scale)
      @origin.x += f * p.x
      @origin.y += f * p.y
      @stage.setOffset(@origin.x, @origin.y)
      @stage.setScale(new_scale)
      @stage.draw()

  # zoom to focus on a box
  zoom_box: (aabb) ->
    min = {x: aabb.min.x - 50, y: aabb.min.y - 50}
    max = {x: aabb.max.x + 50, y: aabb.max.y + 50}
    obj = {width: max.x - min.x, height: max.y - min.y}
    b = compute_dimensions(obj, @bbox, INF)
    @zoom_exp = Math.max(0, Math.min(@zoom_exp_max,
      Math.log(b.scale) / Math.log(2)))
    if @zoom_exp <= 0
      @zoom_reset()
    else
      @origin = min
      @stage.setOffset(@origin.x, @origin.y)
      @stage.setScale(Math.pow(2, @zoom_exp))
      @stage.draw()

  # translate the zoomed in view by some amount
  translate_delta: (x, y, transition=true) ->
    if not @k_loading
      @origin.x += x
      @origin.y += y
      if transition
        @stage.transitionTo(
          offset: clone_pt(@origin)
          duration: 0.1
        )
      else
        @stage.setOffset(@origin.x, @origin.y)
      @stage.draw()

  # translate the view if near the edge
  translate_mouse_click: ->
    if @zoom_exp > 0 and not @k_loading
      p = @stage.getMousePosition()
      p =
        x: p.x / @stage.getWidth()
        y: p.y / @stage.getHeight()
      console.log 'p:', p
      delta = { x: 0, y: 0 }
      factor = @get_zoom_factor()
      if p.x < 0.05
        delta.x = -200 / @get_zoom_factor()
      else if p.x > 0.95
        delta.x = 200 / @get_zoom_factor()
      if p.y < 0.05
        delta.y = -200 / @get_zoom_factor()
      else if p.y > 0.95
        delta.y = 200 / @get_zoom_factor()
      if delta.x != 0 or delta.y != 0
        @translate_delta(delta.x, delta.y)

  error_line: (p1, p2) ->
    el = new Kinetic.Line(
      points: [clone_pt(p1), clone_pt(p2)], opacity: 0.5,
      stroke: "#F00", strokeWidth: 10 / @get_zoom_factor(),
      lineCap: "round")
    @object_layer.add(el)
    @remove(el)

  add_loading: -> if not @k_loading?
    @k_loading = new Kinetic.Text(
      x: 30, y: 30, text: "Loading...", align: "left",
      fontSize: 32, fontFamily: "Helvetica,Verdana,Ariel",
      textFill: "#000")
    @add(@k_loading)
    @draw()

  remove_loading: -> if @k_loading?
    @remove(@k_loading)
    @k_loading = null
    @draw()

  set_segmentation_overlay: (overlay_url, ui, on_load) ->
    if overlay_url?
      overlay_obj = new Image()
      overlay_obj.onload = =>
        if @overlay?
          @overlay.setImage(overlay_obj)
        else
          @overlay = new Kinetic.Image(
            x:0, y: 0, image: overlay_obj,
            width: @size.width, height: @size.height)
          @add_to_layer(@overlay, @overlay_layer, 0.5)
          @overlay.on('mousedown', ->
            if not ui.s.panning
              ui.unselect_poly()
          )
        @draw()
        on_load?()

      overlay_obj.src = overlay_url;
    else
      if @overlay?
        @remove(@overlay)
        @overlay = null

  set_photo: (photo_url, ui, on_load) ->
    @add_loading()
    @photo_obj = new Image()
    @photo_obj.src = photo_url
    @photo_obj.onload = do() => =>
      @remove_loading()
      @size = compute_dimensions(@photo_obj, @bbox)
      #@stage.setWidth(@size.width)
      #@stage.setHeight(@size.height)
      @photo = new Kinetic.Image(
        x: 0, y: 0, image: @photo_obj,
        width: @size.width, height:@size.height)
      @photo_layer.add(@photo)
      @ready = true
      @photo.on('mousedown', ->
        if not ui.s.panning
          ui.unselect_poly()
      )
      @draw()
      on_load?()
