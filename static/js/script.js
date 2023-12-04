function error_message(data, errType) {    
    const wrapper = document.getElementById("alert-wrapper");
    wrapper.innerHTML = [
        `<div class="alert alert-danger alert-dismissible" role="alert">`,
        `   <div>There was an error processing your request! Code: ${data.status}: ${data.statusText}. Error type: ${errType}. Description: ${data.responseJSON.description}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        "</div>",
    ].join("");
}