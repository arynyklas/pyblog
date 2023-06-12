$.ajax({
    url: "/api/posts/list",
    type: "GET",
    async: false,
    success: function(data) {
        for (const post_data of data.posts) {
            console.log(post_data);
            if (post_data.preview_image_url) {
                var img = `<img src="${post_data.preview_image_url}" style="max-width:100px;width:100%">`;
            } else {
                var img = "";
            }
            $("#posts").append(`<li><div class="post"><div class="post_header"><h3 class="post_title_h"><a href="/post/${post_data.id}">${post_data.title}</a></h3><h3 class="post_datetime">${post_data.created_at}</h3></div><div class="post_author"><span>Author:<a role="link" href="/user/${post_data.author.username}">${post_data.author.username}</a></span></div><div class="post_content">${img}<p>${post_data.content}</p></div><div class="post_buttons"><div class="post_button_reactions"></div></div></div></li>`);
        }
    }
});
