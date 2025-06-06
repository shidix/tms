function setWait() { $("body").addClass("loading"); }
function unsetWait() { $("body").removeClass("loading"); }

function ajaxGet(url, datas, target, modal_target, error_function = null)
{
    setWait();
    result=$.ajax({
        url : url,
        type : 'GET',
        data : datas,
        cache : false,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            if (modal_target != "")
            {
                if (data != "")
                {
                    $('#'+modal_target+"-body").html(data);
                    $('#'+modal_target).modal('show');
                }
            }
            else
                if (target != "")
                    $('#'+target).html(data);
            return true;
        },
        error : function(e){
            if (error_function != null)
                error_function(e);
            else
               // show error with sweetalert
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    confirmButtonText: 'Aceptar',
                    background: '#f2f2f2',
                    color: '#333',
                    html: e.responseText,
                });
            return false;
        },
        complete : function(){unsetWait();}
    });
    if (result.status == 200)
        return true;
    else
        return false;
};

function ajaxGetAppend(url, datas, target, modal_target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        cache : false,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            if (modal_target != "")
            {
                $('#'+modal_target+"-body").append(data);
                $('#'+modal_target).modal('show');
            }
            else
                if (target != "")
                    $('#'+target).append(data);
        },
        error : function(e){console.log("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    });
};

function ajaxGetAutosave(url, datas, target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        cache : false,
        beforeSend : function(){},
        success : function(data){
            $("#"+target).html(data).show().fadeTo(5000, 500).slideUp(500, function(){
                $("#"+target).slideUp(500);
            });
        },
        error : function(e){console.log("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};

function ajaxGetEnabled(url, datas, target, modal_target, obj)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        cache : false,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            if (modal_target != "")
            {
                if (data != "")
                {
                    $('#'+modal_target+"-body").html(data);
                    $('#'+modal_target).modal('show');
                }
            }
            else
                if (target != "")
                    $('#'+target).html(data);
            obj.prop("disabled", "")
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    });
};


function ajaxPostAutosave(url, datas, target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'POST',
        data : datas,
        dataType : 'html',
        cache : false,
        beforeSend : function(){},
        success : function(data){
            $("#"+target).html(data).show().fadeTo(5000, 500).slideUp(500, function(){
                $("#"+target).slideUp(500);
            });
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};


function ajaxGetRemove(url, datas, target)
{
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        cache : false,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            if(data != "")
                $('#'+target).html(data);
            else
                $('#'+target).remove();
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){}
    }); 
};

function autoSearch(obj, num_rows=0)
{
    url = obj.data("url");
    target = obj.data("target");
    datas = {'num_rows': num_rows,};
    if (obj.data("related"))
    {
        related = obj.data("related").split(",");
        for(i in related)
        {
            key = $("#"+related[i]).attr('name');
            value = $("#"+related[i]).val();
            datas[key] = value;
        }
    }
    if (obj.data("append"))
        ajaxGetAppend(url, datas, target, '');
    else
        ajaxGet(url, datas, target, '');
}

function uploadObjFile(obj, url, target, obj_id, field, token)
{
    var data = new FormData();
    data.append("file", obj[0].files[0]);
    data.append('obj_id', obj_id);
    data.append('field', field);
    data.append("csrfmiddlewaretoken", token);

    $.ajax({
        url: url,
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        type: 'post',
        success: function (data) {
            $('#'+target).html(data);
            //$('#'+target).trigger('create');
        },
        error : function(e){alert("Error: "+e.responseText);},
    });
}

function uploadMulti(obj, url, target, obj_id, up, token)
{
    var data = new FormData();
    $.each(obj[0].files, function(i, file) {
        data.append("file", file);
    });
    data.append('obj_id', obj_id);
    data.append('target', target);
    data.append('up', up);
    data.append("csrfmiddlewaretoken", token);

    $.ajax({
        url: url,
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        type: 'post',
        success: function (data) {
            if (target.indexOf("alert") >= 0)
            {
                $("#"+target).html(data).fadeTo(5000, 500).slideUp(500, function(){
                    $("#"+target).slideUp(500);
                });
            }
            else
            {
                $('#'+target).html(data);
				$('#'+target).trigger('create');
            }
        },
        error : function(e){alert("Error: "+e.responseText);},
    });
}

function submitForm(frm, target)
{
    setWait();
    $.ajax({
        url: frm.attr('action'),
        type: frm.attr('method'),
        data: frm.serialize(),
        success: function (data) {
            $('#'+target).html(data);
        },
        error: function (data) { alert("Error: "+data.responseText); },
        complete : function(){unsetWait();}
        //complete : function(){$("body").css("cursor", "default");}
    });
}

function closeWin(divName)
{
    setTimeout(function(){
        $(divName).fadeOut('slow');
        setTimeout(function(){
            //window.history.back();
            history.go(-1);
            window.close();
        }, 300);
    }, 2000);
    return false;
}

function closeModal(divName)
{
    setTimeout(function(){
        $(divName).modal('hide');
        setTimeout(function(){
            $('body').removeClass('modal-open');
            $('.modal-backdrop').remove();
        }, 100);
    }, 200);
    return false;
}

function validateField(field)
{
    msg_id = "#" + field.attr("id") + "__msg";
    if (field[0].checkValidity())
    {
        $(msg_id).html("");
        field.removeClass("invalid");
        return true;
    }
    else
    {
        $(msg_id).html("this field is required");
        field.removeClass("valid").addClass("invalid");
        return false;
    }
}

function validateFields(validate_class)
{
    valid = true;
    $("."+validate_class).each(function(){
        if ($(this).data("check"))
        {
            if (!$(this)[0].checkValidity() && !$("#"+$(this).data("check"))[0].checkValidity())
            {
                valid = false;
                validateField($(this));
                validateField($("#"+$(this).data("check")));
            }
        }
        else
            if (!validateField($(this)))
                valid = false;
    });
    return valid;
}

function validateCheckIn()
{
    var ini_date = $("#check_in").val();
    var ini_time = $("#check_in_time").val();
    var end_date = $("#check_out").val();
    var end_time = $("#check_out_time").val();
    var ini = new Date(ini_date+"T"+ini_time)
    var end = new Date(end_date+"T"+end_time)
    if (end < ini)
    {
        $("#check_out__msg").html("This date must be greater than check in");
        field.removeClass("valid").addClass("invalid");
        return false;
    }
    return true;
}

function pushHistory(url) { history.pushState({}, 'main', window.location.href); }

function showAlert(body, close) {
    var text="<p>"+body+"</p><div class='text-end'><button type='button' class='btn btn-marine' data-bs-dismiss='modal'>"+close+"</button></div>";
    $('#common-modal-body').html(text);
    $('#common-modal').modal('show');
}

function UTC2LocalTime(el) {
    const utcString = el.textContent.trim(); 

    // Convertir a objeto Date (formato DD-MM-YYYY HH:mm)
    const [day, month, yearAndTime] = utcString.split("-");
    const [year, time] = yearAndTime.split(" ");
    const isoString = `${year}-${month}-${day}T${time}:00Z`; // formato ISO en UTC
    const date = new Date(isoString);

    // Obtener componentes en hora local
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0'); // Meses 0-11
    const yyyy = date.getFullYear();
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');

    el.textContent = `${dd}-${mm}-${yyyy} ${hh}:${min}`;
}


$(document).ready(()=>{
    $("body").on("keyup", ".autosearch", function(e){
        var obj = $(this);
        setTimeout(function(){
            autoSearch(obj);
        }, 1000);
        e.preventDefault();
    });

    $("body").on("change", ".autosearch_change", function(e){
        var obj = $(this);
        autoSearch(obj);
        e.preventDefault();
    });

    $("body").on("click", ".ark", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]

            ajaxGet(url, datas, target, target_modal, function(e){
                // show error with sweetalert
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    confirmButtonText: 'Aceptar',
                    background: '#f2f2f2',
                    color: '#333',
                    html: e.responseText,
                });
            });


            if (obj.data("show"))
                $("#" + obj.data("show")).show();
            if (obj.data("hide"))
                $("#" + obj.data("hide")).hide();

            e.preventDefault();
            e.stopImmediatePropagation();
        }
    });

    $("body").on("click", ".ark-append", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGetAppend(url, datas, target, target_modal);
            if (obj.data("show"))
                $("#" + obj.data("show")).show();
            e.preventDefault();
        }
    });

    $("body").on("click", ".ark-disabled", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            obj.prop("disabled", "disabled");
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGetEnabled(url, datas, target, target_modal, obj);
            if (obj.data("show"))
                $("#" + obj.data("show")).show();
            if (obj.data("hide"))
                $("#" + obj.data("hide")).hide();

            e.preventDefault();
            e.stopImmediatePropagation();
        }
    });

    $("body").on("change", ".ark_change", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            var url = obj.data("url");
            var value = obj.val();
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {'value': value};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            result = ajaxGet(url, datas, target, target_modal);
            if (obj.data("old-value")) {
                if (result) {
                    obj.data("old-value", value);
                    obj.val(value);
                }
            }

            if (obj.data("clear"))
                clearHtml($("#" + obj.data("clear")));
            e.preventDefault();
        }
    });

    $("body").on("focusout", ".ark_focusout", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            var url = obj.data("url");
            var value = obj.val();
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {'value': value};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGet(url, datas, target, target_modal);

            if (obj.data("clear"))
                clearHtml($("#" + obj.data("clear")));
            e.preventDefault();
        }
    });


    $("body").on("click", ".ark-validate", function(e){
        var obj = $(this);
        var validate_check_in = true;
        if (obj.data("check_in"))
            validate_check_in = validateCheckIn();
        if (validateFields(obj.data("validate")) && validate_check_in)
        {
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGet(url, datas, target, target_modal);
            if (obj.data("show"))
                $("#" + obj.data("show")).show();

            closeModal("#"+obj.data("modal"));
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    });

    $("body").on("change", ".autosave", function(e){
        var obj = $(this);
        msg_id = "#" + obj.attr("id") + "__msg";
        if (obj[0].checkValidity())
        {
            $(msg_id).html("");
            obj.removeClass("invalid");
        }
        else
        {
            $(msg_id).html(obj.attr("title"));
            obj.removeClass("valid").addClass("invalid");
        }

        model_name = obj.data("model-name");
        obj_id = obj.data("obj-id");
        url = obj.data("url");
        target = obj.data("target");
        field = obj.attr("name");
        if (obj.data("ref-field"))
            ref_field = obj.data("ref-field");
        else
            ref_field = "pk";

        if (obj.data("bool"))
            if (obj.data("bool") == "False")
                if (obj.is(':checked'))
                    value = "False";
                else
                    value = "True";
            else
                if (obj.is(':checked'))
                    value = "True";
                else
                    value = "False";
        else
            value = obj.val();

        datas = {'model_name': model_name, 'obj_id': obj_id, 'field': field, 'value': value, "ref_field":ref_field};
        if (obj.data('lang'))
            datas['lang'] = obj.data('lang');
        ajaxGetAutosave(url, datas, target);
        e.preventDefault();
    });

    $("body").on("change", ".autosavepost", function(e){
        var obj = $(this);
        msg_id = "#" + obj.attr("id") + "__msg";
        if (obj[0].checkValidity())
        {
            $(msg_id).html("");
            obj.removeClass("invalid");
        }
        else
        {
            $(msg_id).html(obj.attr("title"));
            obj.removeClass("valid").addClass("invalid");
        }

        model_name = obj.data("model-name");
        obj_id = obj.data("obj-id");
        url = obj.data("url");
        target = obj.data("target");
        field = obj.attr("name");
        if (obj.data("ref-field"))
            ref_field = obj.data("ref-field");
        else
            ref_field = "pk";

        if (obj.data("bool"))
            if (obj.is(':checked'))
                value = "True";
            else
                value = "False";
        else
            value = obj.val();

        datas = {'model_name': model_name, 'obj_id': obj_id, 'field': field, 'value': value, "ref_field":ref_field};
        if (obj.data('lang'))
            datas['lang'] = obj.data('lang');
        ajaxPostAutosave(url, datas, target);
        e.preventDefault();
    });

    $("body").on("click", ".autoremove", function(e){
        if (confirm("Esta seguro/a de que desea borrar el elemento?"))
        {
            model_name = $(this).data("model-name");
            obj_id = $(this).data("obj-id");
            url = $(this).data("url");
            target = $(this).data("target");
            datas = {'model_name': model_name, 'obj_id': obj_id};
            ajaxGetRemove(url, datas, target);
            if ($(this).data("hide"))
                $("#" + $(this).data("hide")).hide();
            e.preventDefault();
        }
    });

    $("body").on("change", ".upload", function(e){
        var obj = $(this);
        var url = obj.data("url");
        var target = obj.data("target");
        var obj_id = obj.data("obj-id");
        var field = "";
        if (obj.data("field"))
            field = obj.data("field");
        var token = obj.data("csrf-token");
        uploadObjFile(obj, url, target, obj_id, field, token);
        e.preventDefault();
    });

    $("body").on("change", ".multiupload", function(e){
        var obj = $(this);
        var url = obj.data("url");
        var target = obj.data("target");
        var obj_id = obj.data("obj-id");
        var up = obj.data("up");
        var token = obj.data("csrf-token");
        uploadMulti(obj, url, target, obj_id, up, token);
        e.preventDefault();
    });


    $("body").on("click", ".saveform", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            form_id = $(this).data("form");
            frm = $('#'+form_id);
            target = $(this).data("target");
            submitForm(frm, target);
            if (obj.data("update"))
                $("#"+obj.data("update")).html($("#"+obj.data("update-val")).val())
            e.preventDefault();
        }
    });

    $("body").on("keyup", ".autocomplete", function(e){
        url = $(this).data("url");
        target = $(this).data("target");
        obj_id = $(this).data("obj_id");
        value = $(this).val()
        datas = {'obj_id': obj_id, 'value': value};
        ajaxGet(url, datas, target, '');
        if ($(this).data("show"))
            $("#" + $(this).data("show")).show();
        e.preventDefault();
    });

    $("body").on("keypress", ".ark_intro", function(e){
        var obj = $(this);
        if(e.which == 13) {
            url = obj.data("url");
            target = obj.data("target");
            value = obj.val();

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            datas['value'] = value;
            ajaxGet(url, datas, target, '');
            obj.val("");
            e.preventDefault();
        }
    });

    $("body").on("click", ".toggle-editor", function(e){
        var editor = $(this).data("editor");
        var source = $(this).data("source");
        $("#editor").toggle();
        $("#source").toggle();
        $(".ql-toolbar").toggle();
        if ($(this).html().indexOf("html") == -1)
            $(this).html("html");
        else
            $(this).html("editor");
        e.preventDefault();
    });

    $("body").on("click", ".toggle-btn", function(e){
        var obj = $(this);
        var target = obj.data("target");
        var text = obj.data("text");
        var textAlt = obj.data("text-alt");

        $("#"+target).slideToggle();
        if (obj.data("id-change"))
            $("#"+$(obj.data("id-change"))).html(obj.html() == textAlt ? text : textAlt);
        else
            obj.html(obj.html() == textAlt ? text : textAlt);
        if (obj.data("set-focus"))
            $("#"+obj.data("set-focus")).focus()
    });

    $("body").on("click", ".toggle-tags", function(e){
        var class_name = $(this).data("class-name");
        if ($(this).is(":checked"))
        {
            $("."+class_name).prop("disabled", true);
            $(this).prop("disabled", false);
        }
        else
            $("."+class_name).prop("disabled", false);
    });

    $("body").on("click", ".copy-to-clipboard", function(e){
        var answer = $("#"+$(this).data("answer"));
        $("#"+$(this).data("src")).select();

        try {
            var ok = document.execCommand('copy');
            if (ok) answer.html('Copied!');
            else    answer.html('Unable to copy!');
        } catch (err) { answer.html('Unsupported Browser!'); }
    });

    // $("body").on("submit", ".post-form", function(e){
    //     var obj = $(this);
    //     if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
    //     {

    //         frm = $(this);
    //         target = $(this).data("target");
    //         error_target = $(this).data("error-target");
    //         // Send the form data using AJAX (post)
    //         $.post(frm.attr('action'), frm.serialize(), function(data) {
    //             $('#'+target).html(data);
    //             //To blink the 
    //             // To enphasize the target
    //             for (var i = 0; i < 3; i++) {
    //                 $('#'+target).fadeTo(100, 0.5).fadeTo(100, 1);
    //             }
                
    //         }
    //         ).fail(function(data) {
    //             if (error_target != "")
    //                 $('#'+error_target).html(data.responseText);
    //             else {
    //                 $('#'+target).html(data.responseText);
    //             }

    //         });
    //         // submitForm(frm, target);
    //         e.preventDefault();
    //     }

    // });

    $("body").on("submit", ".post-form", function(e){
        e.preventDefault(); // Previene el submit estándar

        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm"))) {
            
            var frm = this; // DOM form
            var $frm = $(frm);
            var target = $frm.data("target");
            var error_target = $frm.data("error-target");

            var formData = new FormData(frm); // Incluye todo, incluso archivos

            $.ajax({
                url: $frm.attr('action'),
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                success: function(data) {
                    $('#' + target).html(data);
                    // Para enfatizar el target
                    for (var i = 0; i < 3; i++) {
                        $('#' + target).fadeTo(100, 0.5).fadeTo(100, 1);
                    }
                },
                error: function(data) {
                    if (error_target != "") {
                        $('#' + error_target).html(data.responseText);
                    } else {
                        $('#' + target).html(data.responseText);
                    }
                }
            });
        }
    });


    $("body").on("click", ".ark-alert", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            url = obj.data("url");
            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]

            if (obj.data("icon"))
                icon = obj.data("icon");
            else
                icon = "success"; // success, error, warning, info
            if (obj.data("title"))
                title = obj.data("title");
            else
                title = "Acción realizada";

            $.ajax({
                url : url,
                type : 'GET',
                data : datas,
                cache : false,
                dataType : 'html',
                beforeSend : function(){},
                success : function(data){
                    //alert with sweetalert
                    Swal.fire({
                        icon: icon,
                        title: title,
                        html: data,
                        confirmButtonText: 'Aceptar',
                        background: '#f2f2f2',
                        color: '#333',
                    });
                }
                ,
                error : function(e){
                    // show error with sweetalert
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        confirmButtonText: 'Aceptar',
                        background: '#f2f2f2',
                        color: '#333',
                        html: e.responseText,
                    });
                },
                //complete : function(){unsetWait();}
            });
            e.preventDefault();
        }
    }
    );

    $('body').on('click', '.ark-post', function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            setWait();
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            var function_complete = null;
            if (obj.data("complete"))
                function_complete = obj.data("complete");
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
            if (!csrf_token) {
                csrf_token = obj.data('csrf-token');
                if (!csrf_token) {
                    csrf_token = $('meta[name="csrf-token"]').attr('content');
                }
                if (!csrf_token) {
                    console.error("CSRF token not found. Please ensure it is included in the page.");
                    return;
                }
            }


                // Create form with url as action and data as params and submit
            var form = $('<form>', {
                action: url,
                method: 'POST',
                target: target,
                style: 'display: none;'
            });




            form.append($('<input>', {
                type: 'hidden',
                name: 'csrfmiddlewaretoken',
                value: csrf_token
            }));
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    form.append($('<input>', {
                        type: 'hidden',
                        name: i,
                        value: args[i]
                    }));
            $('body').append(form);

            if ((target_modal == "") && (target == ""))
            {
                form.submit();
                form.remove();
            }
            else
            {
                $.ajax({
                    url: url,
                    type: 'POST',
                    data: form.serialize(),
                    cache: false,
                    dataType: 'html',
                    beforeSend: function(){},
                    success: function(data) {
                        if (target_modal != "")
                        {
                            $('#'+target_modal+"-body").html(data);
                            $('#'+target_modal).modal('show');
                        }
                        else if (target != "")
                            $('#'+target).html(data);
                    },
                    error: function(e) {
                        // show error with sweetalert
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            confirmButtonText: 'Aceptar',
                            background: '#f2f2f2',
                            color: '#333',
                            html: e.responseText,
                        });
                    },
                    complete : function() {
                        if (typeof function_complete == 'function') {
                            function_complete();
                        }
                        unsetWait();
                    }

                });
            }
            if (obj.data("show"))
                $("#" + obj.data("show")).show();

            e.preventDefault();
        }
    }
    );

    $('body').on('click', '.ark-pdf', function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            setWait();
            url = obj.data("url");
            var target = "";
            var filename = "document.pdf"; // Default filename if not specified
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("filename"))
            {
                filename = obj.data("filename");
                // Check if the filename ends with .pdf, if not, append it
                if (!filename.endsWith('.pdf')) {
                    filename += '.pdf';
                }
            }  




            // Launch an AJAX request to get a PDF file
            // If target is not empty, it will be loaded into the target element
            // If target is empty, it will be downloaded as a PDF file
            $.ajax({
                url: url,
                type: 'GET',
                cache: false,
                dataType: 'binary',
                xhrFields: {
                    responseType: 'blob' // Set the response type to blob for binary data
                },
                success: function(data) {
                    if (target != "") {
                        // If target is specified, load the PDF into the target element
                        var blob = new Blob([data], { type: 'application/pdf' });
                        var url = URL.createObjectURL(blob);
                        $('#'+target).html('<iframe src="' + url + '" width="100%" height="600px"></iframe>');
                    } else {
                        // If target is empty, download the PDF file
                        var link = document.createElement('a');
                        link.href = URL.createObjectURL(data);
                        link.download = filename; // Set the desired file name
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    }
                },
                error: function(e) {
                    // show error with sweetalert
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        confirmButtonText: 'Aceptar',
                        background: '#f2f2f2',
                        color: '#333',
                        html: e.responseText,
                    });
                },
                complete : function(){unsetWait();}
            });

            e.preventDefault();
        }
    }
    );


});


