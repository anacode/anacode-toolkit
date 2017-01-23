$(document).ready(function() {
    var link = '<a href="#" class="prompt-toggle">Toggle Prompt</a><br /><br />';
    $(link).prependTo( $("div.code.python,div.highlight-python > .highlight > pre") );
    $(".prompt-toggle").click(function (e) {
        e.preventDefault();
        $(this.parentElement).find("span.gp").toggle();
    });
});