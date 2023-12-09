function error_message(data, errType) {
	const wrapper = document.getElementById("alert-wrapper");

	const content = `Code: ${data.status}: ${data.statusText}.<br/>Error type: ${errType}.<br/>Error Description: ${data.responseJSON.description}<br/>Error info: ${data.responseJSON.info}`;
	wrapper.innerHTML = [
		'<div class="alert alert-danger alert-dismissible" role="alert">',
		'   <div class="d-flex justify-content-between">',
		`       <span class="py-2" style="font-size: 1.25rem;"><i class="px-2 bi bi-exclamation-triangle-fill"></i>Errore: ${data.responseJSON.description}</span>`,
		`       <button type="button" class="btn btn-sm btn-danger d-inline px-3" data-bs-toggle="popover" data-bs-title="${errType}" data-bs-placement="bottom" data-bs-trigger="hover focus" data-bs-html="true" data-bs-content="${content}">Altre informazioni</button>`,
		"   </div>",
		'   <button type="button" style="margin: 1.25rem 0.5rem;" class="btn-close p-2" data-bs-dismiss="alert" aria-label="Close"></button>',
		"</div>",
	].join("");

	const popoverTriggerList = document.querySelectorAll(
		'[data-bs-toggle="popover"]'
	);
	const popoverList = [...popoverTriggerList].map(
		(popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl)
	);
}

function togglePassword(input_id) {
	const toggler = document.getElementById(`${input_id}-toggler`);
	const password = document.getElementById(input_id);
	if (password.getAttribute('type') === 'password') {
		password.setAttribute('type', "text");
		toggler.innerHTML = '<i class="bi bi-eye-slash-fill"></i>';
	} else {
		password.setAttribute('type', "password");
		toggler.innerHTML = '<i class="bi bi-eye-fill"></i>';
	}
}