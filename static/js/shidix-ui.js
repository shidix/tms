// $(document).ready(function () 
$(document).on('click', '.workday-item, .workday-item-accepted', function () {
    var workdayId = $(this).data('id');
    var url = $(this).data('url');
    var csrfmiddlewaretoken = $(this).data('csrfmiddlewaretoken');
    rowClicked = $(this).closest('.list-item-cl');
    $.ajax({
        type: "POST",
        url: url,
        data: {
            'id': workdayId,
            'csrfmiddlewaretoken': csrfmiddlewaretoken
        },
        success: function (response) {

            // Assuming you have a modal with id 'modificationModal' and a div with id 'modalBody' to load the form
            // Show SweetAlert2 modal with the form
            Swal.fire({
                icon: 'info',
                title: 'Solicitar modificación de jornada',
                html: response.html,
                showCancelButton: true,
                showDenyButton: response['deny-url'] ? true : false,
                denyButtonText: 'Historial',
                confirmButtonText: 'Enviar',
                cancelButtonText: 'Cancelar',
                // Don't click outside to close
                allowOutsideClick: false,
                preConfirm: () => {
                    const reason = Swal.getPopup().querySelector('#reason').value;
                    if (!reason) {
                        Swal.showValidationMessage(`Por favor ingrese un motivo`);
                    }
                    return { reason: reason };
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    // Submit the modification request
                    form = Swal.getPopup().querySelector('form');
                    action = form.getAttribute('action');
                    data = $(form).serialize();
                    $.ajax({
                        type: "POST",
                        url: action, // Adjust URL as needed
                        data: data,
                        success: function (submitResponse) {
                            if (submitResponse.updated_html) {
                                rowClicked.replaceWith(submitResponse.updated_html);
                            }
                            Swal.fire('Enviada!', 'Su solicitud de modificación ha sido enviada.', 'success');
                        },
                        error: function (xhr, status, error) {
                            var message = xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : error;
                            Swal.fire('Error!', 'Hubo un error al enviar su solicitud: ' + message, 'error');
                        }
                    });
                }
                else if (result.isDenied) {
                    url_deny = response['deny-url'];
                    // Open modification history
                    $.ajax({
                        type: "GET",
                        url: url_deny,
                        success: function (historyResponse) {
                            var width = historyResponse.width || '90%';
                            Swal.fire({
                                icon: 'info',
                                title: 'Historial de modificaciones',
                                html: historyResponse.html,
                                width: width,
                            });
                        },
                        error: function (xhr, status, error) {
                            Swal.fire('Error!', 'Hubo un error al cargar el historial: ' + error, 'error');
                        }
                    });
                }
            });

        },
        error: function (xhr, status, error) {
            json_response = xhr.responseJSON;
            Swal.fire(
                {
                    icon: 'warning',
                    width: '95%',
                    title: json_response.html || 'Ha ocurrido un error, por favor inténtelo de nuevo.',

                }
            );
        }
    });

});


$(document).on('click', '.ark-sw2-get', function (e) {
    // Reomve previous click handlers to avoid multiple bindings
    // Check if click handler is already bound
    e.preventDefault();
    var url = $(this).data('url');
    btnClicked = $(this);
    $.ajax({
        type: "GET",
        url: url,
        success: function (response) {
            var title = response.title || 'Información';
            var icon = response.icon || 'info';
            var html = response.html || '';
            var width = response.width || '50%';
            Swal.fire({
                icon: icon,
                title: title,
                html: html,
                width: width,
                showDenyButton: response['deny-url'] ? true : false,
                confirmButtonText: response['confirm-url'] ? 'Aceptar' : 'Cerrar',
                denyButtonText: 'Rechazar',
                cancelButtonText: 'Cancelar',
                showCancelButton: response['confirm-url'] || response['deny-url'] ? true : false,
                allowOutsideClick: false,
            }).then((result) => {
                if (result.isConfirmed) {
                    // Handle approval
                    if (!response['confirm-url']) {
                        return;
                    }
                    $.ajax({
                        type: "GET",
                        url: response['confirm-url'],
                        success: function (approveResponse) {
                            Swal.fire('Aprobado!', approveResponse.title || 'Aprobada.', 'success');
                            if (approveResponse.updated_html) {
                                btnClicked.closest('.list-item').html(approveResponse.updated_html);
                            }
                        },
                        error: function (xhr, status, error) {
                            Swal.fire('Error!', 'Hubo un error al aprobar la modificación: ' + error, 'error');
                        }
                    });
                } else if (result.isDenied) {
                    // Handle rejection
                    $.ajax({
                        type: "GET",
                        url: response['deny-url'],
                        success: function (rejectResponse) {
                            Swal.fire('Rechazado!', rejectResponse.title || 'Rechazada.', 'success');
                            if (rejectResponse.updated_html) {
                                btnClicked.closest('.list-item').html(rejectResponse.updated_html);
                            }
                        },
                        error: function (xhr, status, error) {
                            Swal.fire('Error!', 'Hubo un error al rechazar la modificación: ' + error, 'error');
                        }
                    });
                }
            });
        },
        error: function (xhr, status, error) {
            Swal.fire('Error!', 'There was an error fetching the information: ' + error, 'error');
        }
    });
});