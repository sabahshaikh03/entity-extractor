import threading


class ThreadingTool:
    @staticmethod
    def create_and_start_threads(target, args=(), num_threads=1, daemon=True):
        """
        Utility function to create and start multiple threads.

        Args:
            target (callable): The function to be executed by each thread.
            args (tuple): Arguments to be passed to the target function.
            num_threads (int): Number of threads to create.
            daemon (bool): Whether to set threads as daemon threads.
        """
        threads = []
        for index in range(num_threads):
            thread = threading.Thread(target=target, args=(index,))
            if daemon:
                # Daemon thread will exit automatically when the main program exits
                thread.daemon = daemon
            threads.append(thread)
            thread.start()
        return threads

    @staticmethod
    def get_thread_id():
        return threading.current_thread().ident
