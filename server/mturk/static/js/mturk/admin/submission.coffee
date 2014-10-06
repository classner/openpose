$('#content-container').on('click', '.action-show-reject', ->
  $(@).hide()
  $(@).parent('.admin-actions').find('.admin-actions-reject').show()
)

$('#content-container').on('click', '.action-review', ->
  parent = $(@).parents('.admin-actions')[0]
  assignment_id = $(parent).attr('data-assignment')
  action = $(@).attr('data-action')
  message = $(parent).find(".feedback-#{action}").val()

  $.ajax(
    type: 'POST',
    url: window.location,
    dataType: 'json'
    data:
      assignment_id: assignment_id
      action: action
      message: message
    success: (data, status) ->
      if data.result == 'success'
        $(parent).html("<p>Success</p>")
      else
        window.show_modal_error("Error contacting server (#{data})")
    error: ->
      window.show_modal_error("Error contacting server")
  )
)
