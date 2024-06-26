import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

export const accountRouter = createTRPCRouter({
  create: publicProcedure
      .input(z.object({ name: z.string().min(1), user_id: z.string().optional() }))
      .mutation(async ({ ctx, input }) => {
        return ctx.db.accounts.create({
          data: {
            name: input.name,
            user_id: input.user_id,
          },
        });
      }),

  getbyUserId: publicProcedure
    .input(z.object({ user_id: z.string().optional() }))
    .query(({ ctx, input }) => {
      return ctx.db.accounts.findMany({
        where: {
          user_id: input.user_id,
        },
      });
    }),

  update: publicProcedure
    .input(z.object({ id: z.number(), name: z.string().min(1) }))
    .mutation(({ ctx, input }) => {
      return ctx.db.accounts.update({
        where: {
          id: input.id,
        },
        data: {
          name: input.name,
        },
      });
    }),

  delete: publicProcedure
    .input(z.object({ id: z.number() }))
    .mutation(({ ctx, input }) => {
      return ctx.db.accounts.delete({
        where: {
          id: input.id,
        },
      });
    }),

  deleteAll: publicProcedure.mutation(({ ctx }) => {
      return ctx.db.accounts.deleteMany();
    }),
});
