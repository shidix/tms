// $(document).ready(function () 
$(document).on('click', '.workday-item, .workday-item-accepted', function () {
    var workdayId = $(this).data('id');
    var url = $(this).data('url');
    var csrfmiddlewaretoken = $(this).data('csrfmiddlewaretoken');
    rowClicked = $(this).closest('.list-item-cl');
    var replace = false;
    if (rowClicked.length === 0) {
        rowClicked = $(this);
        replace = true;
    }
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
                    title: json_response.title || 'Ha ocurrido un error, por favor inténtelo de nuevo.',
                    html: json_response.html || '',

                    showDenyButton: json_response['deny-url'] ? true : false,
                    denyButtonText: json_response['deny-text'] ? json_response['deny-text'] : 'Historial',
                    confirmButtonText: json_response['confirm-text'] ? json_response['confirm-text'] : 'Cerrar',
                    cancelButtonText: 'Cancelar',
                    showCancelButton: json_response['confirm-url'] && json_response['deny-url'] ? true : false,
                    allowOutsideClick: false,
                    preConfirm: () => {
                        // Just close the modal
                    }
                }
            ).then((result) => {
                if (result.isConfirmed) {
                    url_confirm = json_response['confirm-url'];
                    if (url_confirm) {
                        // Just open the confirm URL
                        $.ajax({
                            type: "GET",
                            url: url_confirm,
                            success: function (confirmResponse) {
                                if (replace) {
                                    if (confirmResponse.updated_html) {
                                        rowClicked.replaceWith(confirmResponse.updated_html);
                                    }
                                } else {
                                    if (confirmResponse.updated_html) {
                                        rowClicked.html(confirmResponse.updated_html);
                                    }
                                }
                                var width = confirmResponse.width || '90%';
                                Swal.fire({
                                    icon: 'info',
                                    title: confirmResponse.title || 'Información',
                                    html: confirmResponse.html,
                                    width: width,
                                });
                            },
                            error: function (xhr, status, error) {
                                Swal.fire('Error!', 'Hubo un error al procesar la solicitud: ' + error, 'error');
                            }
                        });
                    }
                };
                if (result.isDenied) {
                    url_deny = json_response['deny-url'];
                    // Open modification history
                    $.ajax({
                        type: "GET",
                        url: url_deny,
                        success: function (historyResponse) {
                            if (historyResponse.updated_html) {
                                if (replace) {
                                    rowClicked.replaceWith(historyResponse.updated_html);
                                } else {
                                    rowClicked.html(historyResponse.updated_html);
                                }
                            }
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

$(document).on('click', '.ark-email-employee-welcome', function (e) {
    e.preventDefault();
    var url = $(this).data('url');
    var uuid = $(this).data('uuid');
    var csrftoken = $(this).data('csrfmiddlewaretoken');
    var btnClicked = $(this);
    $.ajax({
        type: "POST",
        url: url,
        data: {
            'uuid': uuid,
            'csrfmiddlewaretoken': csrftoken
        },
        success: function (response) {
            Swal.fire('Enviado!', response.message || 'El email de bienvenida ha sido enviado.', 'success');
        },
        error: function (xhr, status, error) {
            var message = xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : error;
            Swal.fire('Error!', 'Hubo un error al enviar el email de bienvenida: ' + message, 'error');
        }
    });
});

$(document).on('click', '.send-manager-email', function (e) {
    e.preventDefault();
    var url = $(this).data('url');
    var uuid = $(this).data('uuid');
    var portal_url = $(this).data('portal-url');
    var csrftoken = $(this).data('csrfmiddlewaretoken');
    var btnClicked = $(this);
    // Show alert to cofirm sending email
    Swal.fire({
        title: 'URL de portal de fichaje',
        html: '<br><strong>' + portal_url + '</strong><br><br> ¿Desea enviar el email con la URL del portal de fichaje a su correo electrónico?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, enviar email',
        cancelButtonText: 'No, no es necesario',
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                type: "POST",
                url: url,
                data: {
                    'uuid': uuid,
                    'csrfmiddlewaretoken': csrftoken
                },
                success: function (response) {
                    Swal.fire('Enviado!', response.message || 'El email con la URL del portal ha sido enviado.', 'success');
                },
                error: function (xhr, status, error) {
                    var message = xhr.responseJSON && xhr.responseJSON.message ? xhr.responseJSON.message : error;
                    Swal.fire('Error!', 'Hubo un error al enviar el email con la URL del portal: ' + message, 'error');
                }
            });
        }
    });
});
