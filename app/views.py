from django.shortcuts import render, get_object_or_404
from app.models import Post, Comments
from app.forms import CommentForm
from django.http import HttpResponseRedirect
from django.urls import reverse

# Create your views here.
def index(request):
    posts = Post.objects.all()
    context = {'posts':posts}
    return render(request, 'app/index.html', context)

def post_page(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comments = Comments.objects.filter(post=post, parent=None)
    form = CommentForm()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():  # Corrected line: Added parentheses to is_valid
            if request.POST.get('parent'):
                # save reply
                parent = request.POST.get('parent')
                parent_obj = Comments.objects.get(id=parent)
                if parent_obj:
                    comment_reply = comment_form.save(commit=False)
                    comment_reply.parent = parent_obj
                    comment_reply.post = post
                    comment_reply.save()
            else:
                comment = comment_form.save(commit=False)
                postid = request.POST.get('post_id')
                post = Post.objects.get(id=postid)
                comment.post = post
                comment.save()
                return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

        if post.view_count is None:
            post.view_count = 1
        else:
            post.view_count += 1
        post.save()

    context = {'post': post, 'form': form, 'comments':comments}
    return render(request, 'app/post.html', context)
