# UI for one scribble
class ScribbleUI
  constructor: (@id, @scribble, @stage) ->
    @line = null

    @stroke_scale = 1.0 / @stage.get_zoom_factor()

  update: (ui, redraw=true) ->
    @add_line()
    if redraw
      @stage.draw()

  add_line: ->
    if @line?
      @line.setPoints(@scribble.points)
      @line.setStrokeWidth(3 * @stroke_scale)
    else
      color = if @scribble.is_foreground then "#00F" else "#0F0"

      @line = new Kinetic.Line(
        points: @scribble.points, opacity: 0, stroke: color,
        strokeWidth: 3 * @stroke_scale, lineJoin: "round")
      @stage.add(@line, 0.5)

  remove_all: -> @remove_line()

  remove_line: -> @stage.remove(@line); @line = null

  # update stroke scale
  update_zoom: (ui, inv_zoom_factor, redraw=true) ->
    @stroke_scale = inv_zoom_factor
    @update(ui, redraw)
