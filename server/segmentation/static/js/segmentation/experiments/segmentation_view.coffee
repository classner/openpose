class SegmentationViewGroup
  constructor: (@view) ->
    @photo_layer = new Kinetic.Layer()
    @view.add_to_stage(@photo_layer)
    @photo_layer.setZIndex(0)
    @overlay_layer = new Kinetic.Layer()
    @view.add_to_stage(@overlay_layer)
    @overlay_layer.setZIndex(1)
    @object_layer = new Kinetic.Layer()
    @view.add_to_stage(@object_layer)
    @object_layer.setZIndex(2)

    @overlay_layer_visible = true

    @size = @view.size

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

  hide: ->
    @photo_layer.hide()
    @overlay_layer.hide()
    @object_layer.hide()

  show: ->
    @photo_layer.show()
    @overlay_layer.show()
    @object_layer.show()

  draw: ->
    @photo_layer.draw()
    @overlay_layer.draw()
    @object_layer.draw()

  destroy: ->
    @photo_layer.destroy()
    @overlay_layer.destroy()
    @object_layer.destroy()

  error_line: (p1, p2) ->
    el = new Kinetic.Line(
      points: [clone_pt(p1), clone_pt(p2)], opacity: 0.5,
      stroke: "#F00", strokeWidth: 10 / @get_zoom_factor(),
      lineCap: "round")
    @object_layer.add(el)
    @remove(el)

  set_segmentation_overlay: (overlay_url, ui, on_load) ->
    if overlay_url?
      @overlay_obj = new Image()
      @overlay_obj.onload = =>
        if @overlay?
          @overlay.setImage(@overlay_obj)
        else
          @overlay = new Kinetic.Image(
            x:0, y: 0, image: @overlay_obj,
            width: @size.width, height: @size.height)
          @add_to_layer(@overlay, @overlay_layer, 0.5)
        @draw()
        on_load?()

      @overlay_obj.src = overlay_url;
    else
      if @overlay?
        @remove(@overlay)
        @overlay = null

  set_photo: (photo_url, ui, on_load) ->
    @photo_obj = new Image()
    @photo_obj.src = photo_url
    @photo_obj.onload = do() => =>
      @size = compute_dimensions(@photo_obj, @view.bbox, INF)
      #@stage.setWidth(@size.width)
      #@stage.setHeight(@size.height)
      @photo = new Kinetic.Image(
        x: 0, y: 0, image: @photo_obj,
        width: @size.width, height:@size.height)
      @photo_layer.add(@photo)
      @ready = true
      @draw()
      on_load?()

  mouse_pos: ->
    p = @view.mouse_pos()

    if not p?
      return p
    else
      x: Math.min(p.x, @size.width)
      y: Math.min(p.y, @size.height)

# Wrapper for Kinetic.Stae
class SegmentationView
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

    @svg_container = d3.select("##{args.container_id}")
      .append("svg")
        .attr("class", 'svg-container')
        .attr("width", @size.width)
        .attr("height", @size.height)
        .attr("style", 'position: absolute; top: 0; left: 0')

    @svg_message = @svg_container
      .append('g')
      .style('opacity', 1e-6)

    @svg_message.append('rect')
      .attr('class', 'message')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', @size.width)
      .attr('height', 115)
      .style('opacity', 0.7)

    @svg_message.append('text')
      .attr('class', 'message')
      .attr('y', 10)

  set_message: (message) ->
    if @cur_message != message
      add_message = =>
        if message?
          text = @svg_message.select('text')
          text.selectAll('tspan').remove()
          for m in message
            text.append('tspan')
              .attr('x', 20)
              .attr('dy', '1.3em')
              .text(m)
          @svg_message
            .transition()
              .duration(250)
              .style('opacity', 1)
              .each('end', => @cur_message = message)
      if @cur_message?
        @cur_message = null
        @svg_message.transition()
          .duration(250)
          .style('opacity', 1e-6)
          .each('end', add_message)
      else
        add_message()

  add_to_stage: (o) ->
    @stage.add(o)

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

