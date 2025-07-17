import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from database.database import get_db
from database.models import Post
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        
    async def start(self):
        """Start the scheduler service"""
        self.running = True
        logger.info("Scheduler service started")
        
        # Load existing scheduled posts
        await self.load_scheduled_posts()
        
        # Start the main loop
        asyncio.create_task(self._main_loop())
        
    async def stop(self):
        """Stop the scheduler service"""
        self.running = False
        for task in self.scheduled_tasks.values():
            task.cancel()
        self.scheduled_tasks.clear()
        logger.info("Scheduler service stopped")
        
    async def _main_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_scheduled_posts()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {str(e)}")
                await asyncio.sleep(60)
                
    async def load_scheduled_posts(self):
        """Load existing scheduled posts from database"""
        try:
            db = next(get_db())
            scheduled_posts = db.query(Post).filter(
                Post.status == 'scheduled',
                Post.scheduled_time > datetime.utcnow()
            ).all()
            
            for post in scheduled_posts:
                await self._schedule_post(post)
                
            logger.info(f"Loaded {len(scheduled_posts)} scheduled posts")
            
        except Exception as e:
            logger.error(f"Error loading scheduled posts: {str(e)}")
            
    async def _schedule_post(self, post: Post):
        """Schedule a post for publishing"""
        try:
            # Calculate delay until scheduled time
            now = datetime.utcnow()
            delay = (post.scheduled_time - now).total_seconds()
            
            if delay <= 0:
                # Post is overdue, publish immediately
                await self._publish_post(post)
            else:
                # Schedule for later
                task = asyncio.create_task(self._delayed_publish(post, delay))
                self.scheduled_tasks[post.id] = task
                logger.info(f"Scheduled post {post.id} for {post.scheduled_time}")
                
        except Exception as e:
            logger.error(f"Error scheduling post {post.id}: {str(e)}")
            
    async def _delayed_publish(self, post: Post, delay: float):
        """Publish post after delay"""
        try:
            await asyncio.sleep(delay)
            await self._publish_post(post)
        except asyncio.CancelledError:
            logger.info(f"Post {post.id} publishing was cancelled")
        except Exception as e:
            logger.error(f"Error in delayed publish for post {post.id}: {str(e)}")
            
    async def _publish_post(self, post: Post):
        """Publish post to target channel"""
        try:
            db = next(get_db())
            
            # Get the post from database to ensure we have latest data
            current_post = db.query(Post).filter(Post.id == post.id).first()
            if not current_post or current_post.status != 'scheduled':
                return
                
            # Prepare text for publishing
            text_to_publish = current_post.edited_text if current_post.edited_text else current_post.original_text
            
            if not text_to_publish:
                logger.error(f"Post {post.id} has no text to publish")
                return
                
            # Publish to target channel
            target_channel = current_post.target_channel or self.bot.config.TARGET_CHANNEL_ID
            if not target_channel:
                logger.error("No target channel configured")
                return
                
            # Send text message
            message = await self.bot.send_message(target_channel, text_to_publish)
            
            # Send media files if any
            if current_post.media_files:
                for media_item in current_post.media_files:
                    try:
                        if media_item['type'] == 'photo':
                            await self.bot.send_photo(target_channel, media_item['file_id'])
                        elif media_item['type'] == 'video':
                            await self.bot.send_video(target_channel, media_item['file_id'])
                    except Exception as e:
                        logger.error(f"Error sending media {media_item['file_id']}: {str(e)}")
                        
            # Update post status
            current_post.status = 'published'
            current_post.published_time = datetime.utcnow()
            db.commit()
            
            # Remove from scheduled tasks
            if post.id in self.scheduled_tasks:
                del self.scheduled_tasks[post.id]
                
            # Notify user
            try:
                await self.bot.send_message(
                    current_post.user.telegram_id,
                    f"✅ Пост успешно опубликован в {target_channel}!"
                )
            except Exception as e:
                logger.error(f"Error notifying user about published post: {str(e)}")
                
            logger.info(f"Post {post.id} published successfully")
            
        except Exception as e:
            logger.error(f"Error publishing post {post.id}: {str(e)}")
            
            # Update post status to error
            try:
                db = next(get_db())
                current_post = db.query(Post).filter(Post.id == post.id).first()
                if current_post:
                    current_post.status = 'error'
                    db.commit()
            except Exception as db_error:
                logger.error(f"Error updating post status: {str(db_error)}")
                
    async def _check_scheduled_posts(self):
        """Check for posts that need to be published"""
        try:
            db = next(get_db())
            now = datetime.now()
            
            # Find posts that should be published now
            posts_to_publish = db.query(Post).filter(
                Post.status == 'scheduled',
                Post.scheduled_time <= now
            ).all()
            
            for post in posts_to_publish:
                await self._publish_post(post)
                
        except Exception as e:
            logger.error(f"Error checking scheduled posts: {str(e)}")
            
    def schedule_post(self, post: Post):
        """Schedule a new post"""
        asyncio.create_task(self._schedule_post(post))
        
    def cancel_post(self, post_id: int):
        """Cancel a scheduled post"""
        if post_id in self.scheduled_tasks:
            self.scheduled_tasks[post_id].cancel()
            del self.scheduled_tasks[post_id]
            logger.info(f"Post {post_id} cancelled")
            
    def get_scheduled_posts(self, user_id: int) -> List[Post]:
        """Get scheduled posts for a user"""
        try:
            db = next(get_db())
            return db.query(Post).filter(
                Post.user_id == user_id,
                Post.status == 'scheduled'
            ).order_by(Post.scheduled_time).all()
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {str(e)}")
            return [] 