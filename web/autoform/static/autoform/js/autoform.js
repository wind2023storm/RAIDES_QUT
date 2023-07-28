window.autoform = {
    context: {},
    field: (field) => $(`[data-autofield="${field}"]`),
    fields: () => $(`[data-autofield]`),
    getContext: function (field) {
        return field.split('.').reduce((obj, key) => obj ? obj[key] : undefined, window.autoform.context);
    },
    setContext: function (field, value) {
        let path = field.split('.');
        let leaf = path.pop();
        let branch = path.reduce( (acc, val) => (acc[val] = acc[val] || {}), window.autoform.context);

        if (branch[leaf] !== value) {
            branch[leaf] = value;
            window.autoform.draw(field, value);
        }
    },
    /**
     * Draws the contents for each autofield of a specific name
     * @param field The field to be drawn (will draw all instances)
     */
    draw: function (field, value) {
        // Iterate auto fields
        window.autoform.field(field).each(function () {
            // Different actions depending on closing tag, e.g., span or img
            const tagName = $(this).prop('tagName');

            if (tagName === 'IMG') {
                let img_dom = $(this)[0]

                if (value) {
                    // Get the image data from the image put into the image field
                    let reader = new FileReader();
                    reader.onload = function (e) {
                        img_dom.src = e.target.result;
                    }
                    // Read that data into the img dom
                    reader.readAsDataURL(value);
                } else {
                    img_dom.src = null;
                }
            } else {
                $(this).text(value);
                // Resize the span to fit the text, or original size if empty
                if (value.length) {
                    this.style.width = value.length + 'ch';
                }
            }
        });
    }
}

$(document).ready(function () {
    /**
     * Auto stacks the documents to fit any white space where different sized screens are used
     * delays until after the document is ready so that auto-sized elements can be stacked corrently
     * implemented with masony @ https://masonry.desandro.com/
     */
    window.setInterval(function () {
        $('.pdf-container').masonry({
            // options
            itemSelector: '.pdf',
            columnWidth: '.pdf',
            gutter: 5,
            fitWidth: true,
        });
    }, 0.001);

    /** Create the popup modal for the autoform before other items are initialized */
    let $popup = $(`
        <div id="autoform-popup" class="autoform-popup">
            <p></p>
            <input/>
            <button name="close" class="btn-ofx-fa btn-ofx-fa-red fa fa-close"></button>
            <button name="accept" class="btn-ofx-fa btn-ofx-fa-green fa fa-check"></button>
        </div>`);

    $('body').append($popup);

    /** Function to auto-populate any spans with the 'data-autofield' attribute used */
    // $.fn.autoPopulate = function () {
    //     let element = $(this)
    //     let name = element.attr('name');
    //
    //     $('span[data-autofield=' + name + ']').each(function () {
    //         // {# Update the spans text #}
    //         let value = element.val();
    //         $(this).text(value);
    //
    //         // {# Resize the span to fit the text, or original size if empty #}
    //         if (value.length) {
    //             this.style.width = value.length + 'ch';
    //         }
    //     });
    //
    //     $('img[data-autofield=' + name + ']').each(function () {
    //         if (element[0].files && element[0].files.length > 0) {
    //             let img_dom = $(this)[0]
    //             let img_file = element[0].files[0];
    //             let reader = new FileReader();
    //
    //             // {# Get the image data from the image put into the image field #}
    //             reader.onload = function (e) {
    //                 img_dom.src = e.target.result;
    //             }
    //             // {# Read that data into the img dom #}
    //             reader.readAsDataURL(img_file);
    //         }
    //     });
    // };

    $('[data-autofield]').on('click keyup', function (e) {
        if (e.type === 'click' || e.which === 13) {
            let type = $(this).data('type');
            let field = $(this).data('autofield');
            let description = $(this).data('description');

            // Figure out handling if the current position puts the dialogue box off the page.
            let x = (e.type === 'click') ? e.pageX - ($popup.width() / 2) : $(this).offset().left - ($(this).width() / 2);
            let y = (e.type === 'click') ? e.pageY - ($popup.height() / 2) : $(this).offset().top - ($(this).height() / 2);

            $popup.css({
                left: x,
                top: y
            }).show();

            let $input;
            switch (type) {
                case 'image':
                    $input = $(`<input type="file" accept="image/*" name="${field}">`);
                    break;
                case 'textarea':
                    $input = $(`<textarea name="${field}" style="resize: vertical">`);  //  placeholder="${description}"
                    $input.val($(this).text());
                    break;
                default:
                    $input = $(`<input type="${type}" name="${field}">`);
                    $input.val($(this).text());
                    break;
            }

            $popup.find('p').text(description);
            $popup.find('input, textarea, image').replaceWith($input);
            $input.focus();
        }
        // Some disgusting focus/hover events for formatting related fields
    }).hover(function () {
        $(`[data-autofield="${$(this).data('autofield')}"]`).addClass('autoform-hover');
    }, function () {
        $(`[data-autofield="${$(this).data('autofield')}"]`).removeClass('autoform-hover');
    }).focusin(function () {
        $(`[data-autofield="${$(this).data('autofield')}"]`).addClass('autoform-hover');
    }).focusout(function () {
        $(`[data-autofield="${$(this).data('autofield')}"]`).removeClass('autoform-hover');
    });

    $('#autoform-popup').on('keyup', 'input', function (e) {
        if (e.keyCode === 13) {  // Enter
            const field = $(this).attr('name');
            const value = $(this).val();
            window.autoform.setContext(field, value, true)
        }
        if (e.keyCode === 27 || e.keyCode === 13) { // Esc or Enter
            $popup.hide();
        }
    }).on('click', 'button', function (e) {
        if ($(this).prop('name') === 'accept') {
            const $input = $popup.find('input, textarea');
            const field = $input.attr('name');
            const type = $input.prop('type')

            window.autoform.setContext(field, type === "file" ? $input[0].files[0] : $input.val(), true)
        }
        $popup.hide();
    });

    /**
     * The native browser print function for generic printing, sometimes the CSS breaks, and page numbers are
     * not added. Primary benefit is that it's printed as normal with text rather than rendered as an image
     * which reduces file size as opposed to the method below
     */
    $.fn.printToPDF = async function () {
        let element = $(this).closest('.pdf');
        let pdfName = element.data('pdf-name');
        let print_area = window.open();

        // {# The CSS has to be loaded into the page for it to be rendered correctly, and the page title #}
        // {# determines the name of the document when printed (or saved to a pdf) #}
        print_area.document.write('<html><head><title>' + pdfName + '</title>');
        print_area.document.write(`<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" type="text/css" />`);
        print_area.document.write(`<link href="/static/appboard/css/appboard.css" rel="stylesheet" type="text/css">`);
        print_area.document.write(`<link href="/static/appboard/css/orefox.css" rel="stylesheet" type="text/css">`);
        print_area.document.write(`<link href="/static/autoform/css/autoform.css" rel="stylesheet" type="text/css">`);
        print_area.document.write('</head><body><div class="pdf">');
        print_area.document.write(element.html());
        print_area.document.write('</div></body></html>');
        print_area.document.close();
        // {# Below are required for IE browsers #}
        print_area.focus();
        setTimeout(function () {
            print_area.print();
            print_area.close();
        }, 200);
    };

    /**
     * The html2pdf version of saving a div to a pdf, this renders the div as an image before saving.
     * however the pdf is saved as an image and vector graphics/text are not used thus text elements are
     * not selectable and can cause massive file sizes if the 'quality' of the image is too high.
     */
    $.fn.saveToPDF = function () {
        // {# Get the pdf element closest to the button #}
        let element = $(this).closest('.pdf');
        let content = element.find('.pdf-content')

        // {# Get some attributes from the elemnt for use #}
        let pdfName = element.data('pdf-name');
        let margins = element.css('padding').match(/(\d+)/g).map(Number)

        // {# Start the process of rendering the html as an image, there are a lot of options here, and can be #}
        // {# read about on the documentation for html2pdf, html2canvas and jsPDF websites/repos #}
        html2pdf().from(element.html()).set({
            filename: pdfName + '.pdf',
            margin: margins,
            pagebreak: {mode: 'avoid-all'},
            image: {type: 'jpeg', quality: 0.98},
            html2canvas: {
                scale: 3,
                scrollY: content.scrollTop(),
                height: content.innerHeight(),
                dpi: 100,
                letterRendering: true,
                useCORS: true,
                ImageQuality: 98,
            },
            jsPDF: {
                unit: 'px',
                format: 'a4',
                orientation: 'portrait',
                hotfixes: ['px_scaling'],
            },
        }).toPdf().get('pdf').then(function (pdf) {
            let numPages = pdf.internal.getNumberOfPages();
            console.log(pdf.internal.pageSize.getHeight())
            for (var i = 1; i <= numPages; i++) {
                pdf.setPage(i);
                pdf.setFontSize(8);
                pdf.setTextColor('#0');
                pdf.text('Page ' + i + ' of ' + numPages, pdf.internal.pageSize.getWidth() / 2, pdf.internal.pageSize.getHeight() - 20);
            }
        }).save();
    };

})